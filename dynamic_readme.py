import feedparser
import requests
import json
import pathlib
import re
import os

root = pathlib.Path(__file__).parent.resolve()

def replace_chunk(content, marker, chunk):
    r = re.compile(
        r"<!\-\- {} starts \-\->.*<!\-\- {} ends \-\->".format(marker, marker),
        re.DOTALL,
    )
    chunk = "<!-- {} starts -->\n{}\n<!-- {} ends -->".format(marker, chunk, marker)
    return r.sub(chunk, content)


def fetch_blog_entries():
    entries = feedparser.parse("https://ubuntu.com/blog/feed/")["entries"]
    return [
        {
            "title": entry["title"],
            "url": entry["link"].split("#")[0],
            "published": entry["published"].split("+")[0],
        }
        for entry in entries
    ]


def fetch_activity():
    org_url = "https://api.github.com/orgs/charmed-kubernetes"
    headers = {"Accept": "application/vnd.github+json"}
    r = requests.get(org_url, headers=headers)
    org = r.json()
    r = requests.get(org["events_url"], headers=headers)
    events = r.json()
    content = []
    for e in events:
        user = ' - [@{}]({})'.format(e['actor']['display_login'],'/'.join(['https://github.com',e['actor']['login']]))
        if e['type'] == 'IssuesEvent':
            action = 'has {} this [issue]({}) in [{}]({}).'.format(e['payload']['action'],
            e['payload']['issue']['html_url'],
            '/'.join(e['payload']['issue']['repository_url'].split('/')[4:]),
            e['payload']['issue']['repository_url'])
            content.append(' '.join([user,action]))
        if e['type'] == 'PushEvent':
            commit_text = e['payload']['commits'][0]['message'].replace('\n',' ')
            commit_text = (commit_text[:57] + '...') if len(commit_text) > 60 else commit_text
            action = 'has pushed the commit **{}** to [{}]({})'.format(commit_text, 
            '/'.join(e['repo']['url'].split('/')[5:]),
            e['repo']['url'].replace('api.github.com/repos','github.com'))
            content.append(' '.join([user,action]))
        if e['type'] == 'PullRequestReviewEvent':
            action = 'has reviewed a [pull request]({}) in the [{}]({}) repository.'.format(e['payload']['pull_request']['html_url'],
            e['repo']['url'].split('/')[-1:][0],
            e['repo']['url'].replace('api.github.com/repos','github.com'))
            content.append(' '.join([user,action]))
    return(content)
    

if __name__ == "__main__":
    readme = root / "README.md"
    readme_contents = readme.open().read()
    entries = fetch_blog_entries()[:6]
    entries_md = "\n".join(
        ["* [{title}]({url}) - {published}".format(**entry) for entry in entries]
    )
    rewritten = replace_chunk(readme_contents, "blog", entries_md)
    activity = fetch_activity()[:10]
    print(activity)
    activity_md = '\n'.join(activity)
    rewritten = replace_chunk(rewritten, "activity", activity_md)
    readme.open("w").write(rewritten)
