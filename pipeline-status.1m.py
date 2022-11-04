#!/opt/homebrew/bin/python3
# -*- coding: UTF-8 -*-

# <xbar.title>CodePipeline Status</xbar.title>
# <xbar.version>v1.0</xbar.version>
# <xbar.author>Sebastian Kruschwitz</xbar.author>
# <xbar.author.github>sebk</xbar.author.github>
# <xbar.desc>Monitor the status of your CodePipeline</xbar.desc>
# <xbar.dependencies>python 3.10.x, boto3</xbar.dependencies>
# <xbar.image></xbar.image>

import boto3

PIPELINE_NAME = 'MyPipeline'

class Pipeline_status:

    def __init__(self) -> None:
        self.cp_client = boto3.client('codepipeline')
        pipeline_result = self.cp_client.get_pipeline_state(name=PIPELINE_NAME)
        self.pipeline_data = self.get_status(result=pipeline_result)

    def get_status(self, result):
        stages = []
        for stage in result['stageStates']:
            name = stage["stageName"]
            actions = []
            for action in stage["actionStates"]:
                action_status = action["latestExecution"]["status"] if "latestExecution" in action else "unknown"
                actions.append({'name': action["actionName"], 'status': action_status})
            status = stage["latestExecution"]["status"] if "latestExecution" in stage else "unknown"
            stages.append({'name': name, 'status': status, 'actions': actions})
        return stages

    def get_status_symbol(self, data) -> str:
        any_progress = any(entry['status'] == 'InProgress' for entry in data)
        if any_progress: return ':hourglass_flowing_sand:'

        any_error = any(entry['status'] == 'Failed' for entry in data)
        if any_error: return ':x:'

        all_succeeded = all(entry['status'] == 'Succeeded' for entry in data)
        if all_succeeded: return ':white_check_mark:'
        
        return ':warning:'

    def get_action_status_symbol(self, action) -> str:
        match action['status']:
            case 'Succeeded': return ':white_check_mark:'
            case 'InProgress': return ':hourglass_flowing_sand:'
            case 'Failed': return ':x:'
            case _: return ':grey_question:' 
        

    def display_status(self):
        emoji = self.get_status_symbol(data=self.pipeline_data)
        status_string = f"{emoji} {PIPELINE_NAME}"
        print(f"{status_string}")

    def display_detailed_status(self):
        for stage in self.pipeline_data:
            stage_emoji = self.get_status_symbol(stage['actions'])
            print(f"{stage_emoji} {stage['name']}")
            for action in stage["actions"]:
                action_emoji = self.get_action_status_symbol(action)
                print(f"-- {action_emoji} {action['name']} ")

if __name__ == '__main__':
    try:
        pipe_status = Pipeline_status()
        pipe_status.display_status()
        print('---')
        pipe_status.display_detailed_status()
    except Exception as ex:
        print(f":warning: Exception executing script. Exception: {ex}")
        raise ex
