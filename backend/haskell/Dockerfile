FROM haskell:9.4

WORKDIR /app

# Copy cabal file first for better caching
COPY haskell-repl.cabal ./

# Build dependencies
RUN cabal update && cabal build --only-dependencies

# Copy source code
COPY Main.hs ./

# Build the application
RUN cabal build

# Expose port
EXPOSE 8000

# Run the application
CMD ["cabal", "run", "haskell-repl"]