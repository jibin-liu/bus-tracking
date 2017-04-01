Onging work to integrate NextBus with Amazon Alexa skills. The source file is in myBus folder.

This project use requests to fetch and parse information from: [next bus](https://www.nextbus.com).

###To prepare source code as an Amazon lambda package
- Pull the code and then use pip to install `requests` and `beautifulsoup4` into the source file directory. For example:
`pip install requests -t .\myBus`
- zip the source code with all other lib, then upload to Amazon lambda
