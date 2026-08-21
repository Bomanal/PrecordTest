FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

ENV MEDRECS_MOCK_GATEWAY=true
ENV MEDRECS_ENVIRONMENT=development
EXPOSE 8000
CMD ["medrecs-uw", "serve"]
