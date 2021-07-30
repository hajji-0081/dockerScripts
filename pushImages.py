
import docker
import sys, getopt
import argparse
import pygogo as gogo
import logging
import os
import getpass

#Prerequisites
#Install Python 3.6 and pip with docker, os, pygogo
#How to run the script python3.6 pushImages.py -f images.txt -v

dockerClientApiFirst = docker.APIClient()
firstUsername = input("Please enter username for the First docker registry: ")
firstPassword = getpass.getpass(prompt='Please enter password for the First docker registry: ', stream=None)
firstregistry = input("Please enter the First docker registry name: ")
dockerClientApiFirst.login(username=firstUsername,password=firstPassword,registry=firstregistry)
dockerClientApiSecond = docker.APIClient()
secondUsername = input("Please enter username for the second docker registry: ")
secondPassword = getpass.getpass(prompt='Please enter password for the second docker registry: ', stream=None)
secondregistry = input("Please enter the second docker registry name: ")
dockerClientApiSecond.login(username=secondUsername,password=secondPassword,registry=secondregistry)


def main(verbose=False):

    parser = argparse.ArgumentParser(description = 'This script is used to push docker images from one cluster to another \n')
    parser.add_argument('--imagefile', '-f',required=True,
                    help='the file that contain images names')
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
       imageFile = open(args.imagefile, 'r')
    except FileNotFoundError as not_found:
       print("File \'"+not_found.filename+"\' Not found !!")
       exit()
    global session
    while True:
        line = imageFile.readline()
        imageNameWithRegistry=line.strip()
        if not line:
           break
        pull_image(imageNameWithRegistry)
        push_image(imageNameWithRegistry,secondregistry)
def pull_image(imageName):
    logger.info("Pulling "+imageName)
    imagePullLog=dockerClientApiFirst.pull(imageName)
    logger.debug(imagePullLog)
    logger.info("** image "+imageName+" pulled**")

def tag_image(imageWithRegistry,secondregistry):
    imageName=imageWithRegistry.split("/")[2]
    imageNameWithoutTag=imageName.split(":")
    logger.info("Tagging "+imageName)
    newImageTag=secondregistry+imageNameWithoutTag[0]
    client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
    image =  client.images.get(imageWithRegistry)
    imageTagingLog=image.tag(newImageTag,imageNameWithoutTag[1])
    logger.debug(imageTagingLog)
    return newImageTag+":"+imageNameWithoutTag[1]

def push_image(imageName,secondregistry):
    logger.info("** Pushing "+imageName+" **")
    imagePushLog=dockerClientApiSecond.push(tag_image(imageName,secondregistry),auth_config = {"username": secondUsername,"password": secondPassword})
    logger.debug(imagePushLog)


if __name__ == '__main__':
    main()
