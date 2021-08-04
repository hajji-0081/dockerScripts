## Install prerequisite

Install python 3.x and pip

```bash
# Using Ubuntu
sudo apt install -y python3-pip

# Using CentOS
yum update -y
yum install -y python3
```
Install the necessary python modules
```bash
pip install docker argparse pygogo logging boto3 botocore
```


## Usage

Prepare file with docker images

```python
# Example
<registry>/docker-image-1:tag
<registry>/docker-image-2:tag

```
