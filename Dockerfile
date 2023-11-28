FROM python:3.11.6-bullseye

RUN mkdir -p /opt/work
COPY ./requirements.txt /opt/work/requirements.txt
WORKDIR /opt/work

RUN apt-get update && apt-get install graphviz -y
RUN pip install -r ./requirements.txt

COPY ./plan-parse.py /opt/work/plan-parse.py

CMD ["streamlit", "run", "plan-parse.py"]
