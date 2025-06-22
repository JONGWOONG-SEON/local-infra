FROM golang:1.24.2 AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build -o webhook .

FROM gcr.io/distroless/static:nonroot
WORKDIR /app
COPY --from=builder /app/webhook .
EXPOSE 8081

ENTRYPOINT ["/app/webhook"]