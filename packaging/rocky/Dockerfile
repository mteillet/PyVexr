# Construction du bundle autonome PyVexr pour Rocky Linux.
#
#   docker build -f packaging/rocky/Dockerfile -t pyvexr-rocky8 .
#
# ou, plus simplement, packaging/rocky/build-docker.sh qui recupere aussi
# l'archive produite.
#
# Par defaut on construit sur Rocky 8 : la glibc 2.28 d'EL8 est plus ancienne
# que celle d'EL9, donc le bundle tourne aussi bien sur Rocky 8 que sur Rocky 9.
ARG BASE_IMAGE=quay.io/rockylinux/rockylinux:8
FROM ${BASE_IMAGE}

ARG PYVEXR_VERSION=""
ENV PYVEXR_VERSION=${PYVEXR_VERSION}
ENV LANG=C.UTF-8

WORKDIR /src

# Etape 1 : paquets systeme, Imath/OpenEXR et virtualenv. Isolee pour que le
# cache Docker ne soit invalide que si le script de build ou les versions des
# dependances changent.
COPY packaging/rocky/build-bundle.sh packaging/rocky/requirements.txt /src/packaging/rocky/
RUN bash /src/packaging/rocky/build-bundle.sh --install-deps --only-deps

# Etape 2 : compilation des modules C++ et generation du bundle.
COPY . /src
RUN bash /src/packaging/rocky/build-bundle.sh --smoke-test

# L'archive se trouve dans /src/dist/
CMD ["/bin/bash", "-c", "ls -lh /src/dist"]
