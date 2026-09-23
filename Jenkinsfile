import org.jenkinsci.plugins.pipeline.modeldefinition.Utils

library identifier: 'JenkinsPipelineUtils', changelog: false

podTemplate(inheritFrom: 'jenkins-agent kaniko', containers: [
    containerTemplates.k8s('k8s')
]) {
    node(POD_LABEL) {
        stage('Cloning repo') {
            checkout scm
        }

        stage("Building NewsFilter") {
            container('kaniko') {
                helmCharts.kaniko([
                    "registry:5000/newsfilter:${currentBuild.number}",
                    "registry:5000/newsfilter:latest"
                ])
            }
        }

        // The build hands its image to Argo CD by pinning it in the deploy repo (argo-cd D53);
        // Argo syncs the commit. HelmCharts no longer deploys this app.
        stage('Write image pins') {
            container('k8s') {
                cicd.writeVersionPins(repo: 'pvginkel/NewsfilterDeploy', pins: [
                    'config/prd/values.yaml': ['images.newsfilter': ":${currentBuild.number}"]
                ])
            }
        }
    }
}
