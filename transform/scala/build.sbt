
scalaVersion := "2.12.18"

// Add all tokenizer dependencies
Compile / unmanagedJars ++= {
  val baseDir = baseDirectory.value
  val libDir = baseDir / "libs/vntokenizer4.1/lib"
  val tokenJar = baseDir / "libs" / "vn.hus.nlp.tokenizer-4.1.1.jar"
  
  (libDir ** "*.jar").get ++ Seq(tokenJar)
}

// Add JAXB and javax.activation for Java 9+
libraryDependencies ++= Seq(
  "com.sun.activation" % "javax.activation" % "1.2.0",
  "javax.xml.bind" % "jaxb-api" % "2.3.1",
  "com.sun.xml.bind" % "jaxb-core" % "2.3.0.1",
  "com.sun.xml.bind" % "jaxb-impl" % "2.3.1",
  "org.apache.spark" %% "spark-sql" % "3.5.0" % "provided",
  "org.apache.spark" %% "spark-core" % "3.5.0" % "provided",
  "org.apache.spark" %% "spark-sql" % "3.5.0" % Test,
  "org.apache.spark" %% "spark-core" % "3.5.0" % Test,
  "org.scalatest" %% "scalatest" % "3.2.15" % Test,
  "org.scalatestplus" %% "scalacheck-1-17" % "3.2.15.0" % Test
)

// Assembly plugin for single fat JAR
assembly / assemblyMergeStrategy := {
  case PathList("META-INF", "services", xs @ _*) => MergeStrategy.concat
  case PathList("META-INF", xs @ _*) => MergeStrategy.discard
  case x => MergeStrategy.first
}

val jarName = "transform-keyword-version-22-21-25-06-2026"
assembly / assemblyOutputPath := baseDirectory.value / s"$jarName.jar"
assembly / mainClass := Some("Main")