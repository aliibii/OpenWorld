#!/usr/bin/python3

import uuid
import json
import yaml
from pathlib import Path
import os
import argparse



def load_config(vmess, compose):
    v2rayConfigPath = vmess
    dockerComposePath = compose
    try:
        file = open(str(v2rayConfigPath), "r", encoding="utf-8")
        config = json.load(file)
    except FileNotFoundError:
        print(f"Error: File {v2rayConfigPath} not found")
    try:
        with open(str(dockerComposePath), "r") as f:
            dockerComposeObject = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: File {dockerComposePath} not found")
    except yaml.YAMLError as e:
        print(f"Error: Failed to parse {dockerComposePath}: {e}")

    return config, dockerComposeObject


def make_config(upstreamUUID, domain, email, config, dockerComposeObject, isSSLEnable):

    config["inbounds"][0]["settings"]["clients"][0]["id"] = upstreamUUID
    dockerComposeObject["services"]["v2ray"]["environment"][
        1
    ] = f"VIRTUAL_HOST={domain}"
    dockerComposeObject["services"]["v2ray"]["environment"][2] = f"LETSENCRYPT_HOST="
    dockerComposeObject["services"]["nginx-proxy-acme"]["environment"][
        0
    ] = f"DEFAULT_EMAIL="
    if isSSLEnable == "yes":
        dockerComposeObject["services"]["v2ray"]["environment"][
            2
        ] = f"LETSENCRYPT_HOST={domain}"
        dockerComposeObject["services"]["nginx-proxy-acme"]["environment"][
            0
        ] = f"DEFAULT_EMAIL={email}"

    content = json.dumps(config, indent=2)
    return content, dockerComposeObject


def save_config(vmess, compose, content, dockerComposeObject):
    open(str(vmess), "w", encoding="utf-8").write(content)
    open(str(compose), "w", encoding="utf-8").write(
        yaml.dump(dockerComposeObject, default_flow_style=False)
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--vc",
        default=Path(__file__).parent.joinpath("v2ray/config/config.json"),
        type=Path,
        help="path to your v2ray config.json",
    )
    p.add_argument(
        "--dc",
        default=Path(__file__).parent.joinpath("docker-compose.yml"),
        type=Path,
        help="path to your docker compose file",
    )
    p.add_argument(
        "--domain", help="Your domain should be either on CloudFlare or Arvan"
    )
    p.add_argument(
        "--cdn",
        help="set `false` if you are using ArvanCDN :))",
        default=True,
        type=bool,
    )

    args = p.parse_args()

    config, dockerComposeObject = load_config(args.vc, args.dc)
    # Check if Docker is installed
    if os.system("which docker") == 0:
        print("Great! You already have docker installed...\nOkaaayyyy Let's go...")
    else:
        print("First time, huh?\n\nI Will try to install docker/compose for you...")
        os.system("curl -fsSL get.docker.com -o get-docker.sh")
        os.system("sh get-docker.sh")
        os.system(
            'sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose'
        )
        os.system("sudo chmod +x /usr/local/bin/docker-compose")

    defaultUUID = config["inbounds"][0]["settings"]["clients"][0]["id"]

    if defaultUUID == "<UPSTREAM-UUID>":
        message = "Upstream UUID: (Leave empty to generate a random one)\n"
    else:
        message = f"Upstream UUID: (Leave empty to use `{defaultUUID}`), you can also type 'new' to setup a new one for you\n Remember you need to regenerate client config by this change as the previous ones will get fucked and cannot be unfucked!! \n"
    upstreamUUID = input(message)
    if upstreamUUID == "":
        if defaultUUID == "<UPSTREAM-UUID>":
            upstreamUUID = str(uuid.uuid4())
        else:
            upstreamUUID = defaultUUID
    elif upstreamUUID == "new":
        upstreamUUID = str(uuid.uuid4())

    # INPUT: Nginx configs

    message = "Enter your domain without http or https: (for example: test.com)\n"
    domain = input(message)
    message = "Enable SSL for this domain? type 'yes' or 'no'. Default is no. if you are using CDN, ignore this.\n"
    isSSLEnable = input(message)
    if isSSLEnable == "yes":
        message = "Enter your email for letsencrypt:\n"
        email = input(message)

    content, dockerComposeObject = make_config(
        upstreamUUID, domain, email, config, dockerComposeObject, isSSLEnable
    )
    save_config(args.vc, args.dc, content, dockerComposeObject)

    print(f"\n---------\nUpstream UUID: {upstreamUUID}")
    print(f"Domain: {domain}")
    if isSSLEnable == "yes":
        print("SSL: enabled")
        print(f"Email: {email}")
    print("---------\n")
    print("\nDone!")
    if not input("Press enter to fire up docker compose ..."):
        os.system("sudo docker-compose up -d --build")
    else:
        print("- Run docker-compose up -d for bringing up services")
    print("\n- Run ./vmess.py to get your vmess links to share to your clients\n")


if __name__ == "__main__":
    main()
