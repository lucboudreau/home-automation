FROM ubuntu:latest

RUN apt update -qq && apt install -y software-properties-common
RUN apt update -qq && apt install -y mosquitto

EXPOSE 1883

CMD mosquitto
