FROM public.ecr.aws/lambda/python:3.12

# System deps for pdfplumber/PyMuPDF
RUN dnf install -y poppler-utils && dnf clean all

COPY pyproject.toml .
RUN pip install --no-cache-dir . mangum

COPY app/ ${LAMBDA_TASK_ROOT}/app/
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/

CMD ["lambda_handler.handler"]
