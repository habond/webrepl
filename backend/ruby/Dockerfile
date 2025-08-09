FROM ruby:3.2-slim

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Gemfile and install dependencies
COPY Gemfile ./
RUN bundle install

# Copy application code
COPY . .

EXPOSE 8000

CMD ["ruby", "app.rb"]