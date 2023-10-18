FROM python:3.10.7-slim-buster as base
LABEL authors="pas-zhukov"
# This flag is important to output python logs correctly in docker!
ENV PYTHONUNBUFFERED 1
# Flag to optimize container size a bit by removing runtime python cache
ENV PYTHONDONTWRITEBYTECODE 1
WORKDIR .

CMD ["python3", "bot.py"]

FROM base as dep-pip
COPY requirements.txt ./
RUN pip install -r requirements.txt
RUN  apt-get update \
  && apt-get install -y wget \
  && rm -rf /var/lib/apt/lists/*
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome-stable_current_amd64.deb
COPY . .