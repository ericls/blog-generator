#!/usr/bin/env python

import datetime as dt
import os
import shutil

from contextlib import contextmanager
from dataclasses import dataclass
from operator import attrgetter
from typing import List, Optional

import frontmatter
import mistletoe
import sass
import yattag

from dotenv import load_dotenv
from slugify import slugify

load_dotenv()

BLOG_TITLE = "the blog"
MY_NAME = os.environ["NAME"]
EMAIL = os.environ["EMAIL"]
HEADER_LINKS = [
    ("github", "https://github.com/p7g"),
    ("linkedin", "https://linkedin.com/pat775"),
]


def header(doc, tag, text, line):
    with tag("header", klass="header"):
        with tag("a", href="/", title="home"):
            line("h1", BLOG_TITLE, klass="header__title")
        line("p", MY_NAME, klass="header__name")

        with tag("section", klass="header__links"):
            for link_text, address in HEADER_LINKS:
                line("a", link_text, href=address, klass="header__links__link")
                text(" ")

        doc.stag("hr")

    return doc


@contextmanager
def base_page(doc, tag, text, line):
    doc.asis("<!DOCTYPE html>")

    with tag("html"):
        with tag("head"):
            doc.stag(
                "meta", name="viewport", content="width=device-width, initial-scale=1"
            )
            doc.stag(
                "link",
                rel="stylesheet",
                href="https://fonts.googleapis.com/css?family="
                "IBM+Plex+Serif:400,400i,700,700i"
                "|Faustina:400,400i,700,700i"
                "|Inconsolata"
                "&display=block",
            )
            doc.stag("link", rel="stylesheet", href="/css/styles.css")
        with tag("body"):
            yield


def home_page(posts: List["Post"]):
    doc, tag, text, line = ttl = yattag.Doc().ttl()

    with base_page(*ttl):
        header(*ttl)

        with tag("main", klass="main"):
            with tag("section", klass="main__post_list"):
                line("h2", "posts", klass="main__post_list__heading")
                for post in posts:
                    with tag("article", klass="main__post"):
                        with tag("a", href=post.url):
                            line("h3", post.title, klass="main__post__title")
                        with tag("small", klass="main__post__date"):
                            line(
                                "time",
                                post.date.strftime("%B %d, %Y"),
                                datetime=post.date.isoformat(),
                            )
                        if post.description is not None:
                            line(
                                "p", post.description, klass="main__post__description",
                            )

    return doc.getvalue()


def post_page(post: "Post"):
    doc, tag, text, line = ttl = yattag.Doc().ttl()

    with base_page(*ttl):
        header(*ttl)

        with tag("main", klass="main"):
            with tag("article", klass="post"):
                with tag("header", klass="post__header"):
                    line("h2", post.title, klass="post__heading")
                    line(
                        "time",
                        post.date.strftime("%B %d, %Y"),
                        time=post.date.isoformat(),
                        klass="post__heading__time",
                    )
                with tag("main", klass="post__main"):
                    doc.asis(post.html)
        with tag("footer", klass="post__footer"):
            doc.stag("hr")
            text("Feedback? ")
            line("a", "Email me", href=f"mailto:{EMAIL}", klass="post__footer__email")

    return doc.getvalue()


@dataclass
class Post:
    title: str
    description: Optional[str]
    date: dt.date
    html: str

    @property
    def slug(self):
        return slugify(self.title)

    @property
    def url(self):
        return f"/posts/{self.slug}"


posts = []

with os.scandir("posts") as it:
    for post_file in it:
        if not post_file.is_file() or post_file.name.startswith("."):
            continue

        with open(post_file.path, "r") as f:
            text = f.read()

        post_raw = frontmatter.loads(text)

        date = post_raw["date"]
        if isinstance(date, str):
            date = dt.date.fromisoformat(date)

        posts.append(
            Post(
                title=post_raw["title"],
                description=post_raw.get("description"),
                date=date,
                html=mistletoe.markdown(post_raw.content),
            )
        )


posts = list(sorted(posts, key=attrgetter("date")))

shutil.rmtree("build")
os.makedirs(os.path.join("build", "posts"), exist_ok=True)

# generate main page
with open(os.path.join("build", "index.html"), "w") as f:
    f.write(home_page(posts))

sass.compile(dirname=("css", os.path.join("build", "css")), output_style="compressed")

for post in posts:
    post_dir = os.path.join("build", "posts", post.slug)
    os.makedirs(post_dir, exist_ok=False)

    with open(os.path.join(post_dir, "index.html"), "w") as f:
        f.write(post_page(post))
