name := "trending-words-job"
version := "1.0.0"
scalaVersion := "2.12.18"

// Add resolvers for VnCoreNLP and other dependencies
resolvers ++= Seq(
  "JCenter" at "https://jcenter.bintray.com/",
  "Maven Central" at "https://repo1.maven.org/maven2/",
  "Aliyun Repository" at "https://maven.aliyun.com/repository/public/",
  Resolver.defaultLocal
)

// Spark and related dependencies
libraryDependencies ++= Seq(
  "org.apache.spark" %% "spark-sql" % "3.5.0" % "provided",
  "org.apache.spark" %% "spark-core" % "3.5.0" % "provided",
  "org.scalatest" %% "scalatest" % "3.2.18" % "test"
)

// Assembly settings for fat JAR
assembly / assemblyJarName := "trending-words-job-assembly.jar"
assembly / test := {}

// Merge strategies for conflicting files in assembly
assembly / assemblyMergeStrategy := {
  case PathList("META-INF", xs @ _*) =>
    xs match {
      case "MANIFEST.MF" :: Nil => MergeStrategy.discard
      case _                    => MergeStrategy.discard
    }
  case "reference.conf"        => MergeStrategy.concat
  case x if x.endsWith(".xml") => MergeStrategy.first
  case x if x.endsWith(".properties") => MergeStrategy.first
  case _                       => MergeStrategy.first
}

// Include resources in assembly
Compile / resourceDirectory := baseDirectory.value / "src" / "main" / "resources"
