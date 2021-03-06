﻿#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script for Coursera resource (pdf/ppt/subtitles/mp4) downloading

Usage:
course-robo-era.py --destination D:\study\coursera\ml --email [coursera email] --password [coursera password] --course-url https://class.coursera.org/ml-2012-002/lecture/index

course-robo-era.py --email [coursera email] --password [coursera password] --course-url https://class.coursera.org/ml-2012-002/lecture/index
by default - destination folder is current folder

---

usage: course-robo-era.py [-h] [--version] --email EMAIL --password PASSWORD --course-url COURSE_URL [--destination DESTINATION]

arguments:
  -h, --help            	show this help message and exit
  --version             	show program's version number and exit
  --email EMAIL         	your email on the course
  --password PASSWORD   	your password on the course
  --course-url COURSE_URL 	URL of course welcome page
  --destination DESTINATION dir where course resources will be stored (by default - current dir will be used)

Author:
Alex Padalka
"""

from collections import defaultdict
import cookielib
from io import open
import logging
import pickle
import urllib2
import os
import re
import sys

import requests
from requests.cookies import cookiejar_from_dict
from bs4 import BeautifulSoup


LOG = logging.getLogger(__name__)

file_name_filter = re.compile(r'\?|%|&|:|\*|\+|,|\'|\\|/|;|\||~')
courseera_filter = re.compile(
    r'https://class.coursera.org/(?P<course_name>[\w-]*)/(?P<welcome_page>.*)')

headers = {
    "DNT": "1",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-us,en;q=0.5",
    "Connection": "keep-alive",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    ,
    "User-agent": "Mozilla/5.0 (Windows NT 6.1; rv:15.0) Gecko/20100101 Firefox/15.0"}

coursera_auth_url = "https://class.coursera.org/%(course_name)s/auth/auth_redirector?type=login&subtype=normal&email=&visiting=%(welcome_page)s"

def parse_page(page_content):
    """
    parse course resource page - getting links to course resources
    """

    resources = []
    headers = page_content.find_all(name='h3', attrs={'class': 'list_header'})
    for header in headers:
        weekly_content = file_name_filter.sub('_', header.contents[0])
        weekly_content = {"week_theme": weekly_content, "content": []}
        resources.append(weekly_content)

        el_group = header.parent.nextSibling
        assert el_group["class"] != "item_section_list"

        for li_node in el_group.find_all(name="li",
            attrs={'class': 'item_row'}):
            res_item = defaultdict()
            weekly_content["content"].append(res_item)

            # lecture title
            title = li_node.find('a', attrs={'class': 'lecture-link'}).\
                    contents[0]
            title = re.sub(r'\n', '', title)
            strip_pos = title.rfind('(')
            res_item["title"] = title[:strip_pos].strip()\
            if strip_pos else title

            # pdf
            pdf_link = li_node.find('a', href=re.compile('.*\.(pdf).*', re.I))
            if pdf_link:
                res_item["pdf"] = pdf_link['href']

            # ppt
            ppt_link = li_node.find('a', href=re.compile('.*\.(ppt).*', re.I))
            if ppt_link:
                res_item["ppt"] = ppt_link['href']

            # subtitles txt
            subtitles_txt_link = li_node.find('a',
                href=re.compile('.*(&format=txt).*', re.I))
            if subtitles_txt_link:
                res_item["subtitles_txt"] = subtitles_txt_link['href']

            # subtitles srt
            subtitles_srt_link = li_node.find('a',
                href=re.compile('.*(&format=srt).*', re.I))
            if subtitles_srt_link:
                res_item["subtitles_srt"] = subtitles_srt_link['href']

            # mp4
            mp4_link = li_node.find('a', href=re.compile('.*\.(mp4).*', re.I))
            if mp4_link:
                res_item["mp4"] = mp4_link['href']

    return resources


def _get_file_name(headers, default=None):
    for key, value in headers.items():
        if "content-disposition" in key.lower():
            results = re.findall(r"\"(.+)\"", value)
            LOG.debug("resource content disposition: %s" % value)
            if results and results[0]:
                return results[0]

    return default


def download_resource(session, dst_folder, url, resource_type):
    LOG.info("Downloading [%s]:%s ... " % (resource_type, url))
    r = session.get(url, allow_redirects=False)
    if r.status_code == 302:
        r = session.get(r.headers['location'])

    file_name = _get_file_name(r.headers)
    if not file_name:
        if not url.endswith("/"):
            unquoted_url = urllib2.unquote(url)
            file_name = unquoted_url[unquoted_url.rfind("/") + 1:]
        else:
            file_name = "%s.%s" % (os.urandom(6), resource_type)

    write_file(dst_folder, file_name, r.content)


def make_local_dir(folder, sub_folder):
    dst_folder = folder if folder.endswith("/") else folder + "/"
    dst_folder += file_name_filter.sub("_", sub_folder)
    if not os.path.exists(dst_folder):
        os.makedirs(dst_folder)

    return dst_folder


def write_file(folder, file_name, content):
    dst_folder = folder if folder.endswith("/") else folder + "/"
    new_file_name = file_name_filter.sub("_", file_name)
    with open("%s%s" % (dst_folder, new_file_name), "wb") as fd:
        fd.write(content)


def course_era_auth(args):
    data = {'email': args["email"], 'password': args["password"],
            'login': 'Login'}

    match_obj = courseera_filter.match(args["course_url"])
    if match_obj is None:
        raise Exception("Course url [%s] is not matched requirements")

    course_name = match_obj.group("course_name")
    course_welcome_page = urllib2.quote("/%s/%s" % (
    match_obj.group("course_name"), match_obj.group("welcome_page")))

    auth_url = coursera_auth_url % {'course_name': course_name,
                                    'welcome_page': course_welcome_page}

    session = requests.session(headers=headers)
    r = session.get(auth_url, allow_redirects=True)

    post_header = dict(headers)
    post_header[
    "Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
    r = session.post(r.url, allow_redirects=True, data=data,
        headers=post_header)

    return session


def download_resources(args):
    session = course_era_auth(args)

    video_listing_content = session.get(args["course_url"]).content
    content = BeautifulSoup(video_listing_content, from_encoding="utf-8")
    resources = parse_page(content)

    lecture_pack_num = 0
    for weekly_resource in resources:
        lecture_pack_num += 1
        LOG.info("Downloading [%s] ..." % weekly_resource["week_theme"])
        dir = make_local_dir(args["destination"], weekly_resource["week_theme"])
        for resource_item in weekly_resource["content"]:
            if resource_item.get("pdf"):
                download_resource(session, dir, resource_item["pdf"], "pdf")

            if resource_item.get("ppt"):
                download_resource(session, dir, resource_item["ppt"], "ppt")

            if resource_item.get("subtitles_txt"):
                download_resource(session, dir, resource_item["subtitles_txt"],
                    "txt")

            if resource_item.get("subtitles_srt"):
                download_resource(session, dir, resource_item["subtitles_srt"],
                    "srt")

            if resource_item.get("mp4"):
                download_resource(session, dir, resource_item["mp4"], "mp4")


def parse_cmd_args():
    """
    parse command line arguments
    """

    current_dir = os.path.dirname(os.path.abspath(__file__))

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version='%(prog)s 1.0a')
    parser.add_argument('--email', help='your email on the course',
        required=True)
    parser.add_argument('--password', help='your password on the course',
        required=True)
    parser.add_argument('--course-url', help='URL of course lectures page',
        required=True)
    parser.add_argument('--destination', default=current_dir,
        help='dir where course resources will be stored, by default - current dir will be used')

    args = parser.parse_args()
    if args.email and args.password and args.course_url and args.destination:
        return vars(args)

    parser.print_help()


def main():
    try:
        import ssl
    except ImportError:
        LOG.error("SSL is not supported by current python env.")
        return

    args = parse_cmd_args()
    if args:
        download_resources(args)
        LOG.info("Process completed ... !")

# TODO:
# * add tests
# * add filter by week range. sample: 1 or 2-8 or 4-
# * add filter by lecture name. sample: "Regression with One Variable"
# * handle session expiration

# * run task in multi-thread mode
# ** http://greenlet.readthedocs.org/en/latest/index.html
# ** http://www.gevent.org/intro.html#installation
if __name__ == "__main__":
    logging.basicConfig(format="%(message)s")
    LOG.setLevel(logging.INFO)

    sys.exit(main())

