FROM ubuntu:22.04 as base
LABEL authors="pas-zhukov"
# This flag is important to output python logs correctly in docker!
ENV PYTHONUNBUFFERED 1
# Flag to optimize container size a bit by removing runtime python cache
ENV PYTHONDONTWRITEBYTECODE 1
WORKDIR .

CMD ["python3", "bot.py"]

FROM base as dep-pip
COPY requirements.txt ./
RUN apt update
RUN DEBIAN_FRONTEND=noninteractive apt-get -yq install python3 python3-pip python3-dev python3-virtualenv
RUN pip install -r requirements.txt
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome-stable_current_amd64.deb
COPY . .
