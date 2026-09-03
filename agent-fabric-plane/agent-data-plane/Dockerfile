FROM maven:3.9.9-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn -q -B -DskipTests dependency:go-offline
COPY src src
# Image build packages only. Skip compiling tests too (-DskipTests still runs testCompile).
# Unit tests run via `mvn test` / CI — not Compose image builds.
RUN mvn -q -B -Dmaven.test.skip=true package

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /app/target/agent-data-plane-0.1.0-SNAPSHOT.jar app.jar
EXPOSE 3007
ENTRYPOINT ["java", "-jar", "app.jar"]
