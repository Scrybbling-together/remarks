commit:=$(shell git rev-parse main)
base_container:=laauurraaa/remarks-bin:${commit}
server_container:=laauurraaa/remarks-server:${commit}

release: build-base build-server upload-bin upload-server
	echo "Releasing app and container at commit ${commit}"

build-base:
	docker build -t ${base_container} -f ./remarks-base/remarks.Dockerfile ..

build-server:
	docker build -t ${server_container} -f ./remarks-server/remarks-server.Dockerfile ./remarks-server

upload-bin:
	docker push ${base_container}

upload-server:
	docker push ${server_container}