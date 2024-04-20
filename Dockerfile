# https://stackoverflow.com/questions/31528384/conditional-copy-add-in-dockerfile
# full means do a full requirements copy
ARG BUILD=base

FROM python:3.11.5-bookworm as slashgpt_base
ONBUILD COPY requirements.txt requirements.txt

FROM python:3.11.5-bookworm as slashgpt_full
ONBUILD COPY requirements/full.txt requirements.txt

# hadolint ignore=DL3006
FROM slashgpt_${BUILD}
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir playsound==1.3.0

WORKDIR /SlashGPT
RUN git clone https://github.com/snakajima/SlashGPT.git

WORKDIR /SlashGPT/SlashGPT
COPY .env .env
