#!/usr/bin/env python

import argparse
import os
from operator import attrgetter
from wsgiref.simple_server import make_server

import sass

from build import get_posts as _get_posts
from build import home_page, post_page

posts_cache = (0, [])


def get_posts_time():
    return sum(os.stat(f).st_mtime for f in os.scandir("posts"))


def get_posts():
    global posts_cache
    posts_time = get_posts_time()
    if posts_cache[0] == posts_time:
        return posts_cache[1]
    new_posts = _get_posts()
    posts_cache = (posts_time, new_posts)
    return posts_cache[1]


def wsgi_application(environ, start_response):
    path = environ["PATH_INFO"]
    if path.endswith(".css"):
        start_response("200 OK", [("Content-Type", "text/css; charset=utf-8")])
        return [sass.compile(filename='.scss'.join(path[1:].rsplit('.css', 1))).encode()]
    posts = get_posts()
    for post in posts:
        if post.url == path:
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            return [post_page(post).encode()]
    if path == "/":
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [home_page(posts).encode()]
    start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
    return ["not found".encode()]


def serve(host: str, port: int):
    with make_server(host, port, wsgi_application) as httpd:
        print(f"Serving HTTP on {':'.join(map(str, httpd.server_address[:2]))}")
        httpd.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serve blog generator")
    parser.add_argument(
        "--host", default="127.0.0.1", type=str, help="bind host", required=False
    )
    parser.add_argument(
        "--port", default="8000", type=int, help="bind port", required=False
    )
    args = parser.parse_args()
    serve(host=args.host, port=args.port)
