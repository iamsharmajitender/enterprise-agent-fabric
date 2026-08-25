# Build from repo root (Compose context ../../.. from docs/run/compose).
# Needs agent-fabric-evals beside agent-data-plane for versioned eval fixtures.
FROM maven:3.9.9-eclipse-temurin-21 AS build
WORKDIR /workspace/agent-data-plane
COPY agent-data-plane/pom.xml .
RUN mvn -q -B -DskipTests dependency:go-offline
COPY agent-data-plane/src src
COPY agent-fabric-evals /workspace/agent-fabric-evals
RUN mvn -q -B test package

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /workspace/agent-data-plane/target/agent-data-plane-0.1.0-SNAPSHOT.jar app.jar
EXPOSE 3007
ENTRYPOINT ["java", "-jar", "app.jar"]
