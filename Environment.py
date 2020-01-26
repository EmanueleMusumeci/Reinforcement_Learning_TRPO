import gym
from gym.envs.registration import registry, register, make, spec
from gym.wrappers import AtariPreprocessing
from collections import namedtuple, defaultdict
import time
import threading
from AtariWrapper import AtariWrapper
from GenericWrapper import GenericWrapper
import matplotlib.pyplot as plt
import copy

from Logger import Logger
##TODO: add a way to store the NN shape

#Il CustomEnvironmentRegister serve a registrare environment con caratteristiche custom
#(come il numero massimo di episodi)

#Named tuple used to store useful info about the custom environment being registered
GenericEnvironmentInfo = namedtuple("EnvironmentInfo","custom_id type render_delay")
AtariEnvironmentInfo = namedtuple("EnvironmentInfo","custom_id type render_delay frame_skip screen_width screen_height crop_height_factor crop_width_factor preprocess")
class CustomEnvironmentRegister:
    def __init__(self, logger, debug=False):
        self.registeredEnvironments = {}
        
        #assert(logger!=None), "You need to create a logger first"
        self.logger = logger
        #if(debug):
        #    logger.add_debug_channel("EnvironmentRegister")

        register(
            id='MountainCarCustom-v0',
            entry_point='gym.envs.classic_control:MountainCarEnv',
            max_episode_steps=5000,      # MountainCar-v0 uses 200
            #reward_threshold=-110.0,
        )
        self.registeredEnvironments["MountainCar-v0"] = GenericEnvironmentInfo("MountainCarCustom-v0","classic",0.0)
        self.log("New environment registered: MountainCar-v0, type: ",self.registeredEnvironments["MountainCar-v0"].type, writeToFile=True, debug_channel="EnvironmentRegister")

        #
        self.registeredEnvironments["MsPacman-v0"] = AtariEnvironmentInfo("MsPacman-v0","atari",
        0.05,
        1,
        210,
        160,
        0,
        0,
        False
        )
        self.log("New environment registered: MsPacman-v0, type: ",self.registeredEnvironments["MsPacman-v0"].type, writeToFile=True, debug_channel="EnvironmentRegister")


        #
        self.registeredEnvironments["MsPacmanPreprocessed-v0"] = AtariEnvironmentInfo("MsPacman-v0","atari",
        0.05,
        1,
        88,
        88,
        0.15,
        0,
        True
        )
        self.log("New environment registered: MsPacmanPreprocessed-v0, type: ",self.registeredEnvironments["MsPacmanPreprocessed-v0"].type, writeToFile=True, debug_channel="EnvironmentRegister")

        #
        self.registeredEnvironments["Pong-v0"] = AtariEnvironmentInfo("Pong-v0","atari",
        0.05,
        1,
        210,
        160,
        0,
        0,
        False
        )
        self.log("New environment registered: Pong-v0, type: ",self.registeredEnvironments["Pong-v0"].type, writeToFile=True, debug_channel="EnvironmentRegister")


        #
        self.registeredEnvironments["PongPreprocessed-v0"] = AtariEnvironmentInfo("Pong-v0","atari",
        0.05,
        1,
        88,
        88,
        0.15,
        0,
        True
        )
        self.log("New environment registered: PongPreprocessed-v0, type: ",self.registeredEnvironments["PongPreprocessed-v0"].type, writeToFile=True, debug_channel="EnvironmentRegister")


        self.log("Registered environments: ",self.registeredEnvironments.keys(), writeToFile=True, debug_channel="EnvironmentRegister")

    def register_environment(self, config_path):
        #Implement uploading environment from path
        return

    def get_environment(self, env_name):
        #Check if we have registered a custom version
        if env_name in self.registeredEnvironments.keys():
            env = gym.make(self.registeredEnvironments[env_name].custom_id)
            env_info = self.registeredEnvironments[env_name]
        
            return env, env_info
        else:
            return gym.make(env_name), None

    def log(self, *strings, writeToFile=False, debug_channel="Generic"):
        if self.logger!=None:
            self.logger.print(strings, writeToFile=writeToFile, debug_channel=debug_channel)


##NOTICE: MODIFY THIS TUPLE IF MORE INFO ARE NEEDED FROM ENVIRONMENT
RolloutTuple = namedtuple("RolloutTuple", "observation reward action action_probabilities")

class Environment:
    def __init__(self, environment_name, logger, use_custom_env_register=True, debug=False, show_preprocessed=False, same_seed=True):
        
        self.debug = debug
        self.environment_name = environment_name

        #assert(logger!=None), "You need to create a logger first"
        self.logger = logger
        #if debug:
        #    self.logger.add_debug_channel("environment")
        
        self.same_seed=same_seed

        if use_custom_env_register:
            self.env_register = CustomEnvironmentRegister(self.logger, debug=True)
            #Create wrapper
            self.log("Using custom environment register", writeToFile=True, debug_channel="environment")
            env, env_info = self.env_register.get_environment(environment_name)
            self.observation_space = env.observation_space
            self.action_space = env.action_space
            self.show_preprocessed = show_preprocessed
            if env_info!=None:
                self.log("Environment info: ",env_info, writeToFile=True, debug_channel="environment")
                self.type = env_info.type
                self.rendering_delay = env_info.render_delay
                
                if(self.type == "atari"):
                    self.frame_skip = env_info.frame_skip
                    self.screen_width = env_info.screen_width
                    self.screen_height = env_info.screen_height

                    self.preprocess = env_info.preprocess
                    if self.preprocess:
                        self.gym_wrapper = AtariWrapper(env, frame_skip=env_info.frame_skip,screen_width=self.screen_width,screen_height=self.screen_height,scale_obs=True,crop_height_factor=env_info.crop_height_factor)
                        #Set the right observation space (if the image is preprocessed it will be grayscale, therefore will only have 1 channel)
                        self.observation_space = self.gym_wrapper.preprocessed_shape()
                    else:
                        self.gym_wrapper = AtariWrapper(env, frame_skip=env_info.frame_skip,screen_width=self.screen_width,screen_height=self.screen_height,scale_obs=False, grayscale_obs=False)
                        #Set the right observation space (if the image is not preprocessed it will have 3 channels)
                        self.observation_space = env.observation_space                    
                else:
                    self.gym_wrapper=GenericWrapper(env)
                    self.preprocess = False

        if not use_custom_env_register or env_info==None:
            self.env_register = None
            self.type = "default"
            self.rendering_delay = 0.0
            self.preprocess = False

            env = gym.make(environment_name)
            self.environment_name = environment_name
            self.gym_wrapper = GenericWrapper(env)

        self.log("self.observation_space: ", self.observation_space, writeToFile=True, debug_channel="environment")

    def __del__(self):
        self.gym_wrapper.close()

    def step(self,action,render=False):
        observation, reward, done, info = self.gym_wrapper.step(action)
        if render: 
            self.render()
        return observation, reward, done, info

    def close(self):
        self.gym_wrapper.close()    

    def reset(self):
        return self.gym_wrapper.reset()

    def render(self):
        if self.preprocess:
            self.gym_wrapper.render(self.show_preprocessed)
        else:
            self.gym_wrapper.render()



    ## NOTICE PARAMETERS THAT MAY BECOME GLOBAL ##
    ##delay
    def collect_rollouts(self, agent, nRollouts, nSteps, render=False):
        def perform_rollout(agent, nSteps, render=False, delay=0.0):
            rollout_info = []

            #get first observation
            old_observation = self.reset()
            done = False
            for i in range(nSteps):
                #Compute next agentStep
                action, action_probabilities = agent.act(old_observation)

                #self.log("Required action space: ", self.action_space, ", Provided action space: ", len(action_probabilities), writeToFile=True, debug_channel="environment")
                #Perform environment step
                observation, reward, done, info = self.gym_wrapper.step(action)

                #Render environment after action
                if render:
                    self.render()
                
                #Save informations to info list
                rollout_info.append(RolloutTuple(old_observation,reward,action,action_probabilities))
                old_observation = observation
                #Terminate prematurely if environment is DONE
                if done:
                    break
            
            return rollout_info, done
        '''
        Collects nRollouts rollouts (different execution of an environment), each one of
        nSteps using a certain agent
        Parameters:
            environment: the gym environment to simulate
            agent: the policy that generates the actions to perform in the simulation
            nRollouts: number of trajectories to collect
            nSteps: number of steps in each trajectory
        Return:
            A dictionary containing:
            -rollouts: a 
        '''
        rollouts = []
        for i in range(nRollouts):
            #self.log("Rollout #"+str(i+1), writeToFile=True, debug_channel="rollouts")
            rollout, done = perform_rollout(agent, nSteps, render=render, delay=self.rendering_delay)
            #self.log("rollout: ", rollout, ", done: ", done, writeToFile=True, debug_channel="rollouts_dump")
            rollouts.append(rollout)
            
            #Terminate prematurely if environment is DONE
            if done:
                continue
        
        return rollouts, done

    def collect_rollouts_multithreaded(self, agent, nRollouts, nSteps, maxThreads, render=False):
        
        rollouts = [[]]*nRollouts
        envs = []
        for _ in range(nRollouts):
            if self.same_seed:
                envs.append(copy.deepcopy(self.gym_wrapper))
            else:
                envs.append(Environment(self.environment_name, self.logger))

        def perform_rollout_thread(agent, nSteps, rolloutNumber, render=False, delay=0.0):
            rollout_info = []
            self.log("Thread number: ", rolloutNumber, writeToFile=True, debug_channel="thread_rollouts")

            #get first observation
            #Necessary because of the implementation produced by my twisted mind
            old_observation = envs[rolloutNumber].reset()
            done = False
            last_action=None
            for i in range(nSteps):
                #Compute next agentStep
                action, action_probabilities = agent.act(old_observation,last_action)
                last_action = action
                #self.log("Required action space: ", envs[rolloutNumber].action_space, ", Provided action space: ", len(action_probabilities), writeToFile=True, debug_channel="environment")
                #Perform environment step
                observation, reward, done, info = envs[rolloutNumber].step(action)

                #Render environment after action
                if render:
                    self.render()
                
                #Save informations to info list
                rollout_info.append(RolloutTuple(old_observation,reward,action,action_probabilities))
                old_observation = observation
                #Terminate prematurely if environment is DONE
                if done:
                    self.log("Thread number: ", rolloutNumber, " terminated because of DONE!!!", debug_channel="thread_rollouts")
                    break
                
            self.log("Thread number: ", rolloutNumber,", Steps performed: ",len(rollout_info), writeToFile=True, debug_channel="thread_rollouts")
            rollouts[rolloutNumber] = rollout_info
        
        current_rollout = 0
        while current_rollout < nRollouts:
            current_thread = 0
            threads = []
            while current_thread < maxThreads and current_rollout < nRollouts:
                self.log("Rollout thread #"+str(current_rollout+1), writeToFile=True, debug_channel="rollouts")
                thread = threading.Thread(target=perform_rollout_thread, args=[agent, nSteps, current_rollout, render, 0.0])
                thread.start()
                threads.append(thread)
                current_thread += 1
                current_rollout += 1
            for thread in threads:
                thread.join() 
        
        return rollouts

    def render_agent(self, agent, nSteps=-1):
        #nSteps = -1 means render until done
        observation = self.reset()
        done = False
        last_action = None
        while not done and nSteps!=0:
            action, _ = agent.act(observation, last_action)
            last_action = action
            print(action)
            observation, reward, done, info = self.step(action)
            time.sleep(self.rendering_delay)
            if done: break
            self.render()
            if nSteps > 0: nSteps = nSteps -1
            
    
    def get_observation_shape(self):
        #return self.space_converter(self.observation_space)
        if self.preprocess:
            self.log("preprocessed_shape: ", self.observation_space, writeToFile=True, debug_channel="environment")
            return self.gym_wrapper.preprocessed_shape()
        else:
            return self.observation_space.shape

    def get_action_shape(self):
        return self.action_space.n
    
    def get_environment_description(self):
        name = self.environment_name
        if self.preprocess:
            name+=".preprocessed"
        return name

    def log(self, *strings, writeToFile=False, debug_channel="Generic"):
        if self.logger!=None:
            self.logger.print(strings, writeToFile=writeToFile, debug_channel=debug_channel)

if __name__ == "__main__":

    env_name = "MountainCar-v0"

    logger = Logger(name=env_name,log_directory="TRPO_project/Testing/Environment") 
    env = Environment(env_name,logger,use_custom_env_register=True,debug=True, show_preprocessed=False, same_seed=True)
    print(env.get_action_shape())
    print(env.get_observation_shape())
