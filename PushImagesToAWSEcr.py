#!/usr/bin/env python
import base64
import boto3
from botocore.exceptions import ClientError
import docker
import sys, getopt
import argparse
import pygogo as gogo
import logging
import os
from botocore.exceptions import ProfileNotFound

#This is a Python script used to push docker images to AWS Ecr.


def main(verbose=False):

    parser = argparse.ArgumentParser(description = 'This script is used to push local docker images into AWS ECR registryIf tarball images do not exist images will be pulled\n')
    parser.add_argument('--region', '-r',required=True,
                    help='aws region')
    parser.add_argument('--imagefile', '-f',required=True,
                    help='the file that contain images names')
    parser.add_argument('--profile', '-p',default='default',
                    help='If ommitted "default" profile will be used')
    parser.add_argument('--nopull', '-np',
                    help='assume latest images are in the local registry, so don\'t pull them before push')
    parser.add_argument('--verbose', '-v', action='store_true', default=False,
                    help='Use this option to activate verbose mode')
    args = parser.parse_args()
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    global logger
    logger = gogo.Gogo(
         '.',
         low_formatter=formatter,
         high_level='error',
         high_formatter=formatter, verbose=args.verbose).logger
    try:
       images = open(args.imagefile, 'r')
    except FileNotFoundError as not_found:
       print("File \'"+not_found.filename+"\' Not found !!")
       exit()
    global session
    try:
        session= boto3.session.Session(profile_name=args.profile)
    except ProfileNotFound:
        logger.error("Profile not found :  Please run the script aws_configure_role.sh")
        exit(1)
    while True:
        line = images.readline()
        image_with_registry=line.strip()
        if not line:
           break
        if "/" in line:
            image = image_with_registry.split("/")
            image_name=image[1]
        create_repo(image_name,args.region,args.profile)
        if args.nopull is None:
            pull_image(image_with_registry)
        tag_image(image_with_registry,args.region,args.profile)
        push_image(image_with_registry,args.region,args.profile)
def pull_image(image_name):
    logger.info("Pulling "+image_name)
    try:
        docker_client_api = docker.APIClient(base_url=os.environ['DOCKER_HOST'])
    except:
        docker_client_api = docker.APIClient()
    image_pul_log=docker_client_api.pull(image_name)
    logger.debug(image_pul_log)
    logger.info("** image "+image_name+" pulled**")

def tag_image(image_with_registry,region,profile):
    image = image_with_registry.split("/")
    image_name=image[1]
    logger.info("Tagging "+image_name)
    client = docker.from_env()
    acountid=session.client('sts').get_caller_identity().get('Account')
    ecr_repo_name=acountid+".dkr.ecr."+region+".amazonaws.com/"+image_name
    image = client.images.get(image_with_registry)
    image_tag_log=image.tag(ecr_repo_name)
    logger.debug(image_tag_log)
    return ecr_repo_name

def create_repo(image_name,region,profile):
    image = image_name.split(":")
    logger.info("Creating Repo "+image_name)
    ecr_client = session.client('ecr', region_name=region)
    image = image_name.split(":")
    try:
        response = ecr_client.create_repository(repositoryName=image[0])
    except ClientError as e:
        if e.response['Error']['Code'] == 'RepositoryAlreadyExistsException':
            logger.warn("Repository %s already exists" % image[0])
        else:
            logger.error("Unexpected error: %s" % e)
    logger.info("Repository"+image[0]+" Created **")


def push_image(image_name,region,profile):
    logger.info("** Pushing "+image_name+" **")
    ecr_client = session.client('ecr', region_name=region)
    acountid=session.client('sts').get_caller_identity().get('Account')
    try:
        docker_client_api = docker.APIClient(base_url=os.environ['DOCKER_HOST'])
    except:
        docker_client_api = docker.APIClient()
    registry='https://'+acountid+'.dkr.ecr.'+region+'.amazonaws.com'
    token = ecr_client.get_authorization_token(registryIds=[acountid])
    username, password = base64.b64decode(token['authorizationData'][0]['authorizationToken']).decode().split(':')
    image_push_log=docker_client_api.push(tag_image(image_name,region,profile),auth_config = {"username": username,"password": password})
    logger.debug(image_push_log)


if __name__ == '__main__':
    main()
