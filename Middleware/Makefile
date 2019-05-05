py_ice:
	mkdir -p communication/out/ice;
	slice2py --output-dir communication/out/ice communication/Bank.ice
py_proto:
	mkdir -p communication/out/proto
	python -m grpc_tools.protoc -Icommunication --python_out=communication/out/proto --grpc_python_out=communication/out/proto Service.proto
java_proto:
	cd service; \
	./gradlew build
run_server:
	python3 server/Server.py
run_client:
	python3 client/Client.py
run_service:
	cd service; \
	./gradlew run
