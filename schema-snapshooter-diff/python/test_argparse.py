import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--test-arg", help="A simple test argument.")
parser.add_argument("--output-format", choices=["text", "json"], help="Test output format.")
args = parser.parse_args()

print(f"Test argument received: {args.test_arg}")
print(f"Output format received: {args.output_format}")