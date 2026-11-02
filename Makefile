.PHONY: test lint run clean

test:
	python3 -m unittest discover -s tests -v

lint:
	python3 -m py_compile archmap/*.py tests/*.py

run:
	python3 -m archmap summary .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -f archmap.html archmap.svg
