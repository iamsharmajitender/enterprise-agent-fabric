FROM maven:3.9.9-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn -q -B -DskipTests dependency:go-offline
COPY src src
RUN mvn -q -B test package

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /app/target/agent-capability-registry-0.1.0-SNAPSHOT.jar app.jar
EXPOSE 3009
ENTRYPOINT ["java", "-jar", "app.jar"]
