import json


def test_should_call():
    data = {
        "name": "call_graphQL",
        "arguments": '{\n  "query": "query {\n    repository(owner: \\"snakajima\\", name: \\"SlashGPT\\") {\n      ref(qualifiedName: \\"main\\") {\n        target {\n          ... on Commit {\n            history(since: \\"2023-09-01T00:00:00Z\\") {\n              totalCount\n              nodes {\n                author {\n                  user {\n                    login\n                  }\n                }\n              }\n            }\n          }\n        }\n      }\n    }\n  }"\n}',
    }
    print(data["arguments"])
    res = json.loads(data["arguments"].replace("\n", ""))
    print(json.dumps(res, indent=2))
    res = json.loads(data["arguments"])
    print(json.dumps(res, indent=2))


test_should_call()
