import graphviz
import time
from openai import OpenAI
import os

client = OpenAI()
client.api_key = os.environ["OPENAI_API_KEY"]
client.organization = os.environ["OPENAI_ORGANIZATION"]

def check_plan(content):
    message = """
以下はPostgreSQLの実行計画です。この実行計画について改善すべき点を挙げてください。
---
{0}
""".format(content)
    messages = [{"role": "user", "content": message}]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return response.choices[0].message.content

def count_leading_spaces(line):
    return len(line) - len(line.lstrip())

def search_parent(source_list, index, level):
    parent = None
    for item in source_list:
        if item["index"] < index and item["level"] == (level - 1):
            if parent is None:
                parent = item
            if parent["index"] < item["index"]:
                parent = item
    return parent

def parse(content):
    lines = []
    i = 0
    for line in content.split("\n"):
        depth = count_leading_spaces(line)
        text = ") AND (\n".join(line.strip().split(") AND ("))
        text = ") OR (\n".join(text.strip().split(") OR ("))
        text = "\n(cost".join(text.strip().split("(cost"))
        if "->" not in text:
            text = text[:100]
        lines.append({"index": i, "depth": depth, "text": text})
        i = i + 1

    lines.sort(key=lambda line: line["depth"])

    level = 0
    current_depth = 0
    for line in lines:
        if current_depth != line["depth"]:
            current_depth = line["depth"]
            level = level + 1
        line["level"] = level

    lines.sort(key=lambda line: line["index"])

    for line in lines:
        parent = search_parent(lines, line["index"], line["level"])
        if parent is not None:
            if "children" not in parent:
                parent["children"] = []
            parent["children"].append(line)

    dot = graphviz.Digraph(comment='plan')
    dot.attr("node", shape="box", width="1", color="black")

    for line in lines:
        dot.node(str(line["index"]), line["text"]) 
    for line in lines:
        if "children" in line:
            for child in line["children"]:
                dot.edge(str(line["index"]), str(child["index"]))
    return dot

import streamlit as st
content = st.text_area("PostgreSQLの実行計画を貼り付けてください")
content = content.strip()
if len(content) > 0:
    dot = parse(content)
    filename = "output/{0}.gv".format(time.strftime('%Y%m%d%H%M%S'))
    dot.render(filename, view=False)
    with open("{0}.pdf".format(filename), "rb") as f:
        buf = f.read()
    st.download_button(
        "Download",
        buf,
        "plan.pdf",
        "application/pdf",
    )
    st.write(check_plan(content))
