
import argparse
import sys
import requests

API_URL = "https://128nsxfbv6.execute-api.ap-south-1.amazonaws.com/default/generate"


def main():
    parser = argparse.ArgumentParser(description="Generate a dlt pipeline from an API description.")
    parser.add_argument("description", nargs="?", help="Plain-English API description")
    parser.add_argument("--file", help="Read the description from a text file instead")
    parser.add_argument("--output", default="generated_pipeline.py", help="Where to save the generated code")
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r") as f:
            description = f.read()
    elif args.description:
        description = args.description
    else:
        print("Error: provide a description as an argument or with --file", file=sys.stderr)
        sys.exit(1)

    print("Sending request to backend...")
    try:
        response = requests.post(API_URL, json={"description": description}, timeout=60)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Request failed: {e}", file=sys.stderr)
        sys.exit(1)

    data = response.json()

    if "error" in data:
        print(f"Backend error: {data['error']}", file=sys.stderr)
        sys.exit(1)

    with open(args.output, "w") as f:
        f.write(data["code"])

    print(f"Generated pipeline saved to {args.output}")


if __name__ == "__main__":
    main()
