FROM openjdk:17-jdk-slim

# Install necessary tools
RUN apt-get update && apt-get install -y curl unzip && rm -rf /var/lib/apt/lists/*

# Install Kotlin compiler
ENV KOTLIN_VERSION=1.9.21
RUN curl -L https://github.com/JetBrains/kotlin/releases/download/v${KOTLIN_VERSION}/kotlin-compiler-${KOTLIN_VERSION}.zip -o kotlin-compiler.zip && \
    unzip kotlin-compiler.zip && \
    mv kotlinc /opt/ && \
    rm kotlin-compiler.zip

# Add Kotlin to PATH
ENV PATH="/opt/kotlinc/bin:${PATH}"

# Install Gradle
ENV GRADLE_VERSION=8.5
RUN curl -L https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip -o gradle.zip && \
    unzip gradle.zip && \
    mv gradle-${GRADLE_VERSION} /opt/gradle && \
    rm gradle.zip

ENV PATH="/opt/gradle/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy Gradle files
COPY build.gradle.kts settings.gradle.kts ./

# Copy source code
COPY src ./src

# Build the application
RUN gradle build --no-daemon

# Expose port
EXPOSE 8000

# Run the application
CMD ["gradle", "run", "--no-daemon"]