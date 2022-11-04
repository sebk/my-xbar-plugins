#!/usr/bin/env PYTHONIOENCODING=UTF-8 /usr/bin/python3
# -*- coding: UTF-8 -*-

# <xbar.title>CodePipeline Status</xbar.title>
# <xbar.version>v1.0</xbar.version>
# <xbar.author>Sebastian Kruschwitz</xbar.author>
# <xbar.author.github>sebk</xbar.author.github>
# <xbar.desc>Monitor the status of your CodePipeline</xbar.desc>
# <xbar.dependencies>python 3.10.x, boto3</xbar.dependencies>
# <xbar.image>https://raw.githubusercontent.com/sebk/my-xbar-plugins/main/pipeline-status.png</xbar.image>
# <xbar.abouturl>https://github.com/sebk/my-xbar-plugins/blob/main/README.md</xbar.abouturl>

# <xbar.var>string(VAR_PIPELINE_NAME="Pipeline-Name"): Name of the pipeline</xbar.var>

import os
import json
import boto3

class PipelineStatus:

    def __init__(self) -> None:
        self.pipeline_name = os.environ.get("VAR_PIPELINE_NAME")
        self.execution_data_cache = {}
        self.cp_client = boto3.client("codepipeline")
        pipeline_result = self.cp_client.get_pipeline_state(name=self.pipeline_name)
        self.pipeline_data = self.get_status(result=pipeline_result)

    def request_execution(self, execution_id):
        if not execution_id:
            return ""
        if execution_id in self.execution_data_cache:
            return self.execution_data_cache[execution_id]

        result = self.cp_client.get_pipeline_execution(pipelineName=self.pipeline_name, pipelineExecutionId=execution_id)
        revisions = result["pipelineExecution"]["artifactRevisions"]
        if len(revisions) > 0:
            message = json.loads(revisions[0]["revisionSummary"])["CommitMessage"]
            self.execution_data_cache[execution_id] = message
            return message
        return ""

    def get_status(self, result):
        stages = []
        for stage in result["stageStates"]:
            status = stage["latestExecution"]["status"] if "latestExecution" in stage else "unknown"

            execution_id = stage["latestExecution"]["pipelineExecutionId"] if "latestExecution" in stage else ""
            message = self.request_execution(execution_id=execution_id)

            actions = []
            for action in stage["actionStates"]:
                action_status = action["latestExecution"]["status"] if "latestExecution" in action else "unknown"
                actions.append({'name': action["actionName"], 'status': action_status})
            stages.append({'name': stage["stageName"], 'status': status, 'actions': actions, 'message': message})
        
        return stages

    def get_status_symbol(self, data) -> str:
        any_progress = any(entry["status"] == "InProgress" for entry in data)
        if any_progress: return ':hourglass_flowing_sand:'

        any_error = any(entry["status"] == "Failed" for entry in data)
        if any_error: return ':x:'

        all_succeeded = all(entry["status"] == "Succeeded" for entry in data)
        if all_succeeded: return ':white_check_mark:'

        return ':warning:'

    def get_action_status_symbol(self, action) -> str:
        # Python >= 3.10.x:
        # match action['status']:
        #     case 'Succeeded': return ':white_check_mark:'
        #     case 'InProgress': return ':hourglass_flowing_sand:'
        #     case 'Failed': return ':x:'
        #     case _: return ':grey_question:'
        # Python 3.9.x:
        if action["status"] == "Succeeded": return ':white_check_mark:'
        if action["status"] == "InProgress": return ':hourglass_flowing_sand:'
        if action["status"] == "Failed": return ':x:'
        return ':grey_question:'

    def display_status(self):
        emoji = self.get_status_symbol(data=self.pipeline_data)
        status_string = f"{emoji} {self.pipeline_name}"
        print(f"{status_string}")

    def display_detailed_status(self):
        for stage in self.pipeline_data:
            stage_emoji = self.get_status_symbol(stage["actions"])
            print(f"{stage_emoji} {stage['name']}")
            print(f"-- {stage['message']}")
            for action in stage["actions"]:
                action_emoji = self.get_action_status_symbol(action)
                print(f"-- {action_emoji} {action['name']} ")

if __name__ == '__main__':
    try:
        pipe_status = PipelineStatus()
        pipe_status.display_status()
        print("---")
        pipe_status.display_detailed_status()
    except Exception as ex:
        print(f":warning: Exception executing script. Exception: {ex}")
        raise ex
