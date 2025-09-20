# ================================
# 1. Base image for AWS Lambda Python 3.11
# ================================
FROM public.ecr.aws/lambda/python:3.11

# ================================
# 2. Set working directory
# ================================
WORKDIR /var/task

# ================================
# 3. Copy requirements and install
# ================================
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir mysql-connector-python fastapi mangum

# ================================
# 4. Copy application code
# ================================
COPY . .

# ================================
# 5. Set Lambda entrypoint (Mangum handler)
# ================================
CMD ["main.handler"]
