FROM python:3.11.5-bookworm

RUN mkdir SlashGPT
WORKDIR /SlashGPT

RUN git clone https://github.com/snakajima/SlashGPT.git

WORKDIR /SlashGPT/SlashGPT

RUN pip install -r requirements.txt
RUN pip install playsound
COPY .env .env