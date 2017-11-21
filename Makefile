init:
	if ! [ -d "./rybot_env" ]; then virtualenv rybot_env -p python3; fi	

	./rybot_env/bin/pip3 install -r requirements.txt

clean:
	rm -r ./rybot_env
