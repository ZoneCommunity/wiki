#!/usr/bin/env python3
import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
CONTENT_DIR = ROOT / "content"
TEMPLATE_DIR = ROOT / "template"
ASSETS_DIR = ROOT / "assets"
DIST_DIR = ROOT / "dist"

GITHUB_REPO = "ZoneCommunity/wiki"
GITHUB_BRANCH = "main"
SITE_NAME = "PPTOS Wiki"
BASE_URL = "https://wiki.pptos.net"


def slugify(text):
    text = re.sub(r"<[^>]+>", "", text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "section"


def parse_frontmatter(text):
    """Return (frontmatter dict, body). Frontmatter is --- key: value ---."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].strip()
    fm = {}
    for line in raw.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fm[key.strip()] = value.strip().strip('"').strip("'")
    return fm, text[end + 4:].lstrip("\n")


def parse_inline(text):
    """Inline Markdown: code, bold, italic, images, links. Input is raw text."""
    text = html.escape(text)
    # Inline code first, so nothing inside it is re-parsed.
    parts = []

    def _code(m):
        parts.append(m.group(1))
        return "\x00%d\x00" % (len(parts) - 1)

    text = re.sub(r"`([^`]+)`", _code, text)
    # Images: ![alt](src "title") - title is optional.
    text = re.sub(
        r'!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)',
        lambda m: '<img src="%s" alt="%s"%s>' % (
            m.group(2),
            html.escape(m.group(1), quote=True),
            (' title="%s"' % html.escape(m.group(3), quote=True)) if m.group(3) else "",
        ),
        text,
    )
    # Links: [text](url)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)",
        lambda m: '<a href="%s">%s</a>' % (m.group(2), m.group(1)),
        text,
    )
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    # Restore inline code placeholders.
    for i, code in enumerate(parts):
        text = text.replace("\x00%d\x00" % i, "<code>%s</code>" % code)
    return text


def parse_markdown(md):
    """Return (html, headings, plain_text). Headings are (level, text, id)."""
    lines = md.splitlines()
    out = []
    headings = []
    plain = []
    i = 0
    in_code = False
    code_lang = ""
    code_buf = []
    in_table = False
    in_section = False

    def close_table():
        nonlocal in_table
        if in_table:
            out.append("</tbody></table>")
            in_table = False

    while i < len(lines):
        line = lines[i]

        # Fenced code blocks.
        if line.strip().startswith("```"):
            if in_code:
                pre_html = "<pre><code>%s</code></pre>" % html.escape("\n".join(code_buf))
                code_buf = []
                in_code = False
                # A code block directly followed by an image sits
                # beside it, instead of stacking above it.
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines) and re.match(r"^!\[.*\]\(.*\)\s*$", lines[j].strip()):
                    img_line = lines[j].strip()
                    img_html = parse_inline(img_line)
                    alt = re.match(r"^!\[([^\]]*)\]", img_line).group(1)
                    caption = "<figcaption>%s</figcaption>" % html.escape(alt) if alt else ""
                    out.append('<div class="media-row">%s<figure>%s%s</figure></div>' % (pre_html, img_html, caption))
                    plain.append(alt)
                    i = j + 1
                else:
                    out.append(pre_html)
                    i += 1
            else:
                close_table()
                in_code = True
                code_lang = line.strip()[3:].strip()
                code_buf = []
                i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        stripped = line.strip()
        if not stripped:
            close_table()
            i += 1
            continue

        # Headings.
        m = re.match(r"^(#{1,3})\s+(.*)$", line)
        if m:
            close_table()
            level = len(m.group(1))
            text = m.group(2).strip()
            hid = slugify(text)
            # The page title (h1) is rendered by the template, not the body.
            if level == 1:
                plain.append(text)
                i += 1
                continue
            headings.append((level, text, hid))
            # h2 starts a new section, so its figures stay inside it
            # instead of spilling down beside the next section. h3
            # stays inside the current section.
            if level == 2:
                if in_section:
                    out.append("</section>")
                out.append("<section>")
                in_section = True
            out.append('<h%d id="%s">%s</h2>' % (level, hid, parse_inline(text)) if level == 2 else '<h%d id="%s">%s</h%d>' % (level, hid, parse_inline(text), level))
            plain.append(text)
            i += 1
            continue

        # Horizontal rule.
        if stripped in ("---", "***", "___"):
            close_table()
            out.append("<hr>")
            i += 1
            continue

        # Blockquote.
        if stripped.startswith("> "):
            close_table()
            quote = []
            while i < len(lines) and lines[i].strip().startswith("> "):
                quote.append(lines[i].strip()[2:])
                plain.append(lines[i].strip()[2:])
                i += 1
            out.append("<blockquote><p>%s</p></blockquote>" % "<br>".join(parse_inline(q) for q in quote))
            continue

        # Tables: header row, separator row, then data rows.
        if stripped.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s\-:|]+\|\s*$", lines[i + 1]):
            close_table()
            header = [c.strip() for c in stripped.strip("|").split("|")]
            out.append('<table><thead><tr>%s</tr></thead><tbody>' % "".join(
                "<th>%s</th>" % parse_inline(c) for c in header))
            plain.append(" ".join(header))
            in_table = True
            i += 2
            continue
        if in_table and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            out.append("<tr>%s</tr>" % "".join("<td>%s</td>" % parse_inline(c) for c in cells))
            plain.append(" ".join(cells))
            i += 1
            continue
        close_table()

        # Unordered lists.
        if re.match(r"^[-*]\s+", stripped):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(lines[i].strip()[2:].strip())
                plain.append(lines[i].strip()[2:].strip())
                i += 1
            out.append("<ul>%s</ul>" % "".join("<li>%s</li>" % parse_inline(x) for x in items))
            continue

        # Ordered lists.
        if re.match(r"^\d+\.\s+", stripped):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                plain.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            out.append("<ol>%s</ol>" % "".join("<li>%s</li>" % parse_inline(x) for x in items))
            continue

        # Images on their own line become a figure, so they get a caption.
        # A video file (.mp4, .webm) uses the same syntax and becomes a
        # <video> player inside the figure instead.
        # Consecutive images (blank lines allowed between them) become
        # a row of figures side by side instead of stacking.
        if re.match(r"^!\[.*\]\(.*\)\s*$", stripped):
            imgs = [stripped]
            j = i + 1
            while True:
                k = j
                while k < len(lines) and not lines[k].strip():
                    k += 1
                if k < len(lines) and re.match(r"^!\[.*\]\(.*\)\s*$", lines[k].strip()):
                    imgs.append(lines[k].strip())
                    j = k + 1
                else:
                    break
            figs = []
            for s in imgs:
                alt = re.match(r"^!\[([^\]]*)\]", s).group(1)
                src = re.match(r"^!\[[^\]]*\]\(([^)]*)\)$", s).group(1)
                if src.lower().endswith((".mp4", ".webm")):
                    # preload="auto" so the whole video is buffered: seeking
                    # needs byte-range requests, and not every static server
                    # supports them, so a metadata-only preload leaves the
                    # timeline unseekable until the file has played through.
                    media_html = '<video controls preload="auto" src="%s"></video>' % html.escape(src)
                else:
                    media_html = parse_inline(s)
                caption = "<figcaption>%s</figcaption>" % html.escape(alt) if alt else ""
                figs.append("<figure>%s%s</figure>" % (media_html, caption))
                plain.append(alt)
            if len(figs) > 1:
                out.append('<div class="figure-row">%s</div>' % "".join(figs))
            else:
                out.append(figs[0])
            i = j
            continue

        # Paragraph: gather consecutive non-blank lines.
        para = []
        while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith("#") \
                and not lines[i].strip().startswith("```") and not lines[i].strip().startswith("|") \
                and not re.match(r"^[-*]\s+", lines[i].strip()) and not re.match(r"^\d+\.\s+", lines[i].strip()) \
                and not lines[i].strip().startswith("> "):
            para.append(lines[i].strip())
            plain.append(lines[i].strip())
            i += 1
        if para:
            out.append("<p>%s</p>" % " ".join(parse_inline(p) for p in para))
        else:
            i += 1

    close_table()
    if in_section:
        out.append("</section>")
    return "\n".join(out), headings, " ".join(plain)


def build_page_lookup(pages):
    lookup = {}
    # Pass 1: titles where the filename matches the title exactly
    for page in pages:
        if page["path"].stem == page["title"] and page["title"] not in lookup:
            lookup[page["title"]] = page["url"]
    # Pass 2: every other title, first wins
    for page in pages:
        if page["title"] not in lookup:
            lookup[page["title"]] = page["url"]
    # Pass 3: filename stems
    for page in pages:
        stem = page["path"].stem
        if stem not in lookup:
            lookup[stem] = page["url"]
    return lookup


def link_version(name, lookup):
    # Values like "Mesolite/ZoneCore" link on the first part only
    first = name.split("/")[0].strip()
    path = lookup.get(first) or lookup.get(name)
    if path:
        return '<a href="%s">%s</a>' % (path, html.escape(name))
    return html.escape(name)


def render_infobox(fm, lookup):
    """Infobox from frontmatter. Names that match a page link out."""
    # Only the keys listed here render in the infobox. Any other
    # frontmatter key is silently ignored, so adding a field to a
    # page means adding a row here too. A row only shows when the
    # page actually sets that key.
    rows = [
        ("core", "Core", True),
        ("status", "Status", False),
        ("developer", "Developer", False),
        ("source_model", "Source model", False),
        ("license", "License", False),
        ("official_website", "Official website", False),
        ("initial_development", "Initial development", False),
        ("initial_release", "Initial release", False),
        ("latest_release", "Latest release", False),
        ("latest_preview", "Latest preview", False),
        ("latest_development", "Latest development", False),
        ("latest_build", "Latest build", False),
        ("current_branch", "Current version", True),
        ("current_core", "Current core", True),
        ("longest_developed", "Longest developed", True),
        ("languages", "Languages", False),
    ]
    cells = []
    # images is a comma-separated list, so a page can stack several
    # pictures in the infobox. image still works for a single one.
    # image_captions is a semicolon-separated list in the same order,
    # one caption under each image (semicolons, because captions
    # themselves can contain commas).
    images = [s.strip() for s in fm.get("images", "").split(",") if s.strip()]
    if not images and fm.get("image"):
        images = [fm["image"]]
    captions = [s.strip() for s in fm.get("image_captions", "").split(";") if s.strip()]
    for i, src in enumerate(images):
        cells.append('<tr><td class="infobox-image" colspan="2"><img src="%s" alt="%s"></td></tr>' % (
            html.escape(src, quote=True), html.escape(fm.get("title", ""), quote=True)))
        if i < len(captions):
            cells.append('<tr><td class="infobox-caption" colspan="2">%s</td></tr>' % html.escape(captions[i]))
    for key, label, is_version in rows:
        if key not in fm:
            continue
        value = fm[key]
        if key == "official_website":
            url = value if value.startswith(("http://", "https://")) else "https://" + value
            rendered = '<a href="%s">%s</a>' % (html.escape(url, quote=True), html.escape(value))
        elif is_version:
            rendered = link_version(value, lookup)
        else:
            rendered = html.escape(value)
        cells.append("<tr><th>%s</th><td>%s</td></tr>" % (label, rendered))
    if not cells:
        return ""
    return ('<table class="infobox"><caption class="infobox-title">%s</caption><tbody>%s</tbody></table>'
            % (html.escape(fm.get("title", "")), "".join(cells)))


def render_contents(headings):
    if not headings:
        return "<p>No sections on this page yet.</p>"
    items = ['<li><a href="#top">(Top)</a></li>']
    for level, text, hid in headings:
        items.append('<li class="level-%d"><a href="#%s">%s</a></li>' % (
            level, hid, html.escape(text)))
    return "<ul>\n%s\n</ul>" % "\n".join(items)


def page_url(md_path):
    """content/ZoneOS/Mesolite.md -> /ZoneOS/Mesolite/ ; content/index.md -> /"""
    rel = md_path.relative_to(CONTENT_DIR).with_suffix("")
    parts = list(rel.parts)
    if parts == ["index"]:
        return "/"
    return "/" + "/".join(parts) + "/"


def breadcrumb(url_path, title):
    """Show the wiki.pptos.net/ZoneOS/<Version> path, with links."""
    if url_path == "/":
        return "wiki.pptos.net"
    parts = [p for p in url_path.strip("/").split("/") if p]
    crumbs = ['<a href="/">wiki.pptos.net</a>']
    acc = ""
    for part in parts[:-1]:
        acc += "/" + part
        crumbs.append('<a href="%s/">%s</a>' % (acc, html.escape(part)))
    crumbs.append(html.escape(parts[-1]))
    return " / ".join(crumbs)


def collect_pages():
    pages = []
    for md_path in sorted(CONTENT_DIR.rglob("*.md")):
        text = md_path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        url = page_url(md_path)
        title = fm.get("title") or url.strip("/").split("/")[-1].replace("-", " ") or "PPTOS Wiki"
        pages.append({"path": md_path, "fm": fm, "body": body, "url": url, "title": title})
    return pages


def child_pages(page, all_pages):
    """Subpages: Markdown files in the folder that shares this page's name.

    content/ZoneOS/Mesolite.md has subpages in content/ZoneOS/Mesolite/.
    content/ZoneOS.md has subpages in content/ZoneOS/ (the version files).
    """
    child_dir = page["path"].with_suffix("").parent / page["path"].stem
    # For a top-level page like ZoneOS.md, the folder is content/ZoneOS/.
    if not child_dir.is_dir():
        return []
    children = []
    for child in sorted(child_dir.glob("*.md")):
        match = next((p for p in all_pages if p["path"] == child), None)
        if match:
            children.append(match)
    return children


def build_page(page, all_pages, layout, lookup):
    fm = page["fm"]
    body_html, headings, plain_text = parse_markdown(page["body"])

    # Automatic Subpages section from child files
    children = child_pages(page, all_pages)
    if children:
        items = "".join(
            '<li><a href="%s">%s</a></li>' % (c["url"], html.escape(c["title"]))
            for c in children)
        body_html += '\n<h2 id="subpages">Subpages</h2>\n<ul>%s</ul>' % items

    description = (fm.get("description") or plain_text[:200]).strip()
    description = re.sub(r"\s+", " ", description)

    rel_md = page["path"].relative_to(ROOT).as_posix()
    edit_url = "https://github.com/%s/edit/%s/%s" % (GITHUB_REPO, GITHUB_BRANCH, rel_md)
    history_url = "https://github.com/%s/commits/%s/%s" % (GITHUB_REPO, GITHUB_BRANCH, rel_md)

    page_html = layout
    page_html = page_html.replace("{{TITLE}}", html.escape(page["title"]))
    page_html = page_html.replace("{{DESCRIPTION}}", html.escape(description, quote=True))
    page_html = page_html.replace("{{BREADCRUMB}}", breadcrumb(page["url"], page["title"]))
    page_html = page_html.replace("{{CONTENTS}}", render_contents(headings))
    page_html = page_html.replace("{{INFOBOX}}", render_infobox(fm, lookup))
    page_html = page_html.replace("{{CONTENT}}", body_html)
    page_html = page_html.replace("{{EDIT_URL}}", edit_url)
    page_html = page_html.replace("{{HISTORY_URL}}", history_url)
    page_html = page_html.replace("{{PAGE_PATH}}", page["url"])
    # The "All versions" tab is per-OS, not ZoneOS-only: any top-level
    # page (an OS, e.g. ZoneOS, MyOS, Windows) gets one when it has a
    # Versions page, e.g. content/MyOS/Versions.md -> /MyOS/Versions/.
    # The homepage never gets the tab. On the Versions page itself,
    # All versions is the active tab and Article links back to the
    # OS's main article; on other pages of that OS, Article is active.
    parts = [p for p in page["url"].split("/") if p]
    os_slug = parts[0] if parts else ""
    versions_url = "/%s/Versions/" % os_slug if os_slug else ""
    has_versions = any(p["url"] == versions_url for p in all_pages) if versions_url else False
    if has_versions and page["url"] == versions_url:
        article_tab = '<a class="tab" href="/%s/">Article</a>' % os_slug
        all_versions_tab = '<a class="tab active" href="%s">All versions</a>' % versions_url
    elif has_versions and page["url"].startswith("/%s/" % os_slug):
        article_tab = '<a class="tab active" href="%s">Article</a>' % page["url"]
        all_versions_tab = '<a class="tab" href="%s">All versions</a>' % versions_url
    else:
        article_tab = '<a class="tab active" href="%s">Article</a>' % page["url"]
        all_versions_tab = "" 
    page_html = page_html.replace("{{ARTICLE_TAB}}", article_tab)
    page_html = page_html.replace("{{ALL_VERSIONS_TAB}}", all_versions_tab)
    return page_html, plain_text


def build_404(layout):
    content = (
        '<p>There is no page at this address on the PPTOS Wiki. '
        'It may have been moved, renamed, or mistyped.</p>\n'
        '<p>Try one of these instead:</p>\n'
        '<ul>'
        '<li><a href="/">PPTOS Wiki</a> - the homepage</li>'
        '<li><a href="/ZoneOS/">ZoneOS</a> - the main ZoneOS article</li>'
        '<li><a href="/ZoneOS/Versions/">All versions</a> - every ZoneOS version, in order</li>'
        '</ul>\n'
        '<p>Or use the search box at the top of the page.</p>'
    )
    page_html = layout
    page_html = page_html.replace("{{TITLE}}", "Page not found")
    page_html = page_html.replace(
        "{{DESCRIPTION}}", "This page does not exist on the PPTOS Wiki.")
    page_html = page_html.replace(
        "{{BREADCRUMB}}", '<a href="/">wiki.pptos.net</a> / Page not found')
    page_html = page_html.replace("{{CONTENTS}}", "")
    page_html = page_html.replace("{{INFOBOX}}", "")
    page_html = page_html.replace("{{CONTENT}}", content)
    page_html = page_html.replace(
        "{{EDIT_URL}}", "https://github.com/%s" % GITHUB_REPO)
    page_html = page_html.replace(
        "{{HISTORY_URL}}", "https://github.com/%s/commits/%s" % (GITHUB_REPO, GITHUB_BRANCH))
    page_html = page_html.replace("{{PAGE_PATH}}", "/")
    page_html = page_html.replace(
        "{{ARTICLE_TAB}}", '<a class="tab active" href="/">Article</a>')
    page_html = page_html.replace("{{ALL_VERSIONS_TAB}}", "")
    return page_html


def main():
    layout = (TEMPLATE_DIR / "layout.html").read_text(encoding="utf-8")
    pages = collect_pages()
    if not pages:
        raise SystemExit("No Markdown files found under content/")
    lookup = build_page_lookup(pages)

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)

    search_index = []
    for page in pages:
        page_html, plain_text = build_page(page, pages, layout, lookup)
        if page["url"] == "/":
            out_path = DIST_DIR / "index.html"
        else:
            out_path = DIST_DIR.joinpath(*page["url"].strip("/").split("/")) / "index.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(page_html, encoding="utf-8")
        search_index.append({
            "title": page["title"],
            "path": page["url"],
            "text": re.sub(r"\s+", " ", plain_text)[:3000],
        })
        print("built %s -> %s" % (page["path"].relative_to(ROOT), out_path.relative_to(DIST_DIR)))

    (DIST_DIR / "search.json").write_text(
        json.dumps(search_index, indent=2, ensure_ascii=False), encoding="utf-8")

    (DIST_DIR / "404.html").write_text(build_404(layout), encoding="utf-8")
    print("built 404.html")

    # Assets: images, plus the template CSS and JS.
    if ASSETS_DIR.is_dir():
        shutil.copytree(ASSETS_DIR, DIST_DIR / "assets", dirs_exist_ok=True)
    shutil.copyfile(TEMPLATE_DIR / "style.css", DIST_DIR / "assets" / "style.css")
    shutil.copyfile(TEMPLATE_DIR / "script.js", DIST_DIR / "assets" / "script.js")

    cname = ROOT / "CNAME"
    if cname.exists():
        shutil.copyfile(cname, DIST_DIR / "CNAME")
    (DIST_DIR / ".nojekyll").write_text("", encoding="utf-8")

    print("wrote %d pages, search.json, assets/ to %s" % (len(pages), DIST_DIR))


if __name__ == "__main__":
    main()
