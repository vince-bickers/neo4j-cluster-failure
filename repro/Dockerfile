FROM python:3.7

ADD requirements.txt .
RUN pip install -r requirements.txt

ADD miniserv.py .
ADD commands.py .
CMD ["python3", "miniserv.py"]
