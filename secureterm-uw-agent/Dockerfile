FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

ENV SECURETERM_MOCK_GATEWAY=true
ENV SECURETERM_ENVIRONMENT=development
EXPOSE 8000
CMD ["secureterm-uw", "serve"]
