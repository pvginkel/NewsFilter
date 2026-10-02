// Builds the newsfilter image and pins it into NewsfilterDeploy, which Argo CD syncs to prd.
//
// Controller config:
//   - Job: NewsFilter
//   - SCM: pvginkel/NewsFilter, branch main
//   - Script Path: Jenkinsfile

library identifier: 'JenkinsPipelineUtils', changelog: false

pipeline {
    agent {
        kubernetes {
            inheritFrom 'jenkins-agent kaniko'
            yamlMergeStrategy merge()
            yaml podYaml(templates: ['k8s'])
        }
    }

    options {
        disableConcurrentBuilds(abortPrevious: true)
        skipDefaultCheckout()
        timeout(time: 60, unit: 'MINUTES')
        timestamps()
    }

    triggers {
        githubPush()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build newsfilter image') {
            steps {
                container('kaniko') {
                    script {
                        helmCharts.kaniko2(destinations: [
                            "registry:5000/newsfilter:${currentBuild.number}",
                            'registry:5000/newsfilter:latest',
                        ])
                    }
                }
            }
        }

        stage('Write image pins') {
            steps {
                container('k8s') {
                    script {
                        cicd.writeVersionPins(repo: 'pvginkel/NewsfilterDeploy', pins: [
                            'config/prd/values.yaml': ['images.newsfilter': ":${currentBuild.number}"],
                        ])
                    }
                }
            }
        }
    }
}
