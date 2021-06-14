# AGM
The AGM repository contains three main pieces of code:
- An automated task planner based on graph models (as oposed to classic predicate-based models - hypregraphs). The planner is called _AGGLPlanner_.
- A service to manage graph-like world models for robots, a.k.a. Deep State Representation (DSR). The service, called _AGMExecutive_, can run as a mere world-model representation service or it can be integrated with AGGLPlanner so that the executive can also be in charge of updating the plan for a list of subscribers.
- A C++/Python library, _libAGM_, designed to work with these graph-based world models. The documentation of the API of the library can be found in [http://grammarsandrobots.org/AGM/](http://grammarsandrobots.org/AGM/)).

Scientific literature about the agent-based approach followed in AGM:
- A Perception-Aware Architecture for Autonomous Robots [link](https://journals.sagepub.com/doi/full/10.5772/61742)
- Use and advances in the Active Grammar-based Modeling architecture [link](https://www.jopha.ua.es/article/view/10353)

Scientific works using AGM:
- Socially aware robot navigation system in human-populated and interactive environments based on an adaptive spatial density function and space affordances [link](https://www.sciencedirect.com/science/article/abs/pii/S0167865518303052)
- Planning object informed search for robots in household environments [link](https://ieeexplore.ieee.org/document/8374184)
- Integrating planning perception and action for informed object
search [link](https://link.springer.com/epdf/10.1007/s10339-017-0828-3?author_access_token=CVPOdUFdgRfqllS5r5rrz_e4RwlQNchNByi7wbcMAY6ZCO2AMOjuFaGGz3wUqPcFeLtCAWkh6N6MCgsFfVlic0YSAw0xeFlR4evhO1cPGH-U5nveL9xNv2pVUH9uOBS31hB4dNsc2MFlqm9asshY2w%3D%3D)
- The CORTEX cognitive robotics architecture: Use cases [link](https://www.sciencedirect.com/science/article/pii/S1389041717300347?via%3Dihub)
- Planning Human-Robot Interaction for Social Navigation in Crowded Environments [link](https://link.springer.com/chapter/10.1007/978-3-319-99885-5_14)

## Software requirements
To run AGMExecutive, whether as a DSR or as a DSR+Executive, you will need:
- a working RoboComp Installation [https://github.com/robocomp/robocomp/](https://github.com/robocomp/robocomp/)
- libxml2: sudo apt-get install libxml2-dev
- thriftpy: pip install thriftpy

## Installation
The Installation script will ask you if you want to have RoboComp support.
You will need to answer "yes" unless you are only interested in the planner (AGGLPlanner).

We have had users reporting a falling installation. Most of the times running "make" in the build directory fixes the problem. We'll look into it.

Remember to set the $ROBOCOMP environment variable. If you are not going to actively develop RoboComp, setting it as "/opt/robocomp" is a good idea.

~~~
git clone https://github.com/ljmanso/AGM
cd AGM
sh compile.sh
~~~



## How to set up a DSR server
The goal of a DSR service is to support communication between agents through a graph-like shared model. We call such models Deep State Representations (DSRs). To this end, AGMExecutive relies on a ZeroC-Ice publication/subscription server called IceBox. RoboComp provides a small script, _rcnode_, to easily run an IceBox server. The first step is to run rcnode. The following command runs IceBox on the background (don't expect any output):
~~~
rcnode &
~~~

The next step is to write a configuration file for _AGMExecutive_. The following is an example configuration file of for AGMExecutive working as a DSR service:
~~~
# E N D P O I N T S
AGMExecutive.Endpoints=tcp -p 10198
AGMCommonBehavior.Endpoints=tcp -p 11198
AGMAgentTopic.Endpoints=tcp -p 12198

# R E M O T E    P R O X I E S
IceStormProxy = IceStorm/TopicManager:tcp -h localhost -p 9999

# D S R  -  C O N F I G U R A T I O N
AutostartAGGLPlannerServer = off
DoNotPlan = True
InitialModelPath =   /PATH/TO/initialModel.xml

# A G E N T S
AGENTS = agenta,agentb
agenta = agmcommonbehavior:tcp -h localhost -p 10330
agentb = agmcommonbehavior:tcp -h localhost -p 10331

# ZeroC-Ice parameters
Ice.ThreadPool.Client.Size=50
Ice.ThreadPool.Server.Size=50
Ice.MessageSizeMax=2000480
Ice.Override.ConnectTimeout=1000
Ice.Override.CloseTimeout=1000
Ice.Override.Timeout=1000
~~~

The content of the AGMExecutive configuration file won't change much if you only intend to run AGMExecutive as a DSR service. Still, there are a few variables that you will have to modify. The first variable is _DoNotPlan_. It tells AGMExecutive whether you want to use it just as a DSR:

~~~
DoNotPlan = True
~~~

AGMExecutive will expect you to provide an XML file with an initial world model. The path of the file is specified in the variable _InitialModelPath_:
~~~
InitialModelPath =   /PATH/TO/initialModel.xml
~~~

The content of the file deserves its own section, so we'll look into that in the future (see section [Writing initial models](#Writing initial models)). Meantime we will assume that the initial model of the robot is a graph where the robot is represented by a _robot_ symbol with an identifier _1_.
~~~
<AGMModel>
    <symbol id="1" type="robot">
    </symbol>
</AGMModel>
~~~

The only thing left to configure is the pool of agents that the DSR will work with. First, we will populate a variable called _AGENTS_ with a comma separated list of the names of the agents. Then, for each agent we will write a similar line where the only thing that changes will be the port where the agent will listen to for updates. We will go back to that in section [Modifying the models and subscribing to changes](#Modifying the models and subscribing to changes):
~~~
AGENTS = room_handler,human_interaction_handler,objects_handler
agenta = agmcommonbehavior:tcp -h localhost -p 10330
agentb = agmcommonbehavior:tcp -h localhost -p 10331
~~~

Once you are done with the files you can run the server as:
~~~
python2 AGMExecutive_robocomp.py ~/devel/socnav/robocomp_agm/etc/dsr.conf 
~~~

## Generating agents
Generating AGM/CORTEX agents does not differ much from other RoboComp components. The main characteristic of agents is that their CDSL file should use the _agmagent_ option.
~~~
options agmagent;
~~~

The following is an example of a _Python_ agent using a _Qt_ (which is optional too).
~~~
Component agent_name
{
    Communications
    {
    };
    language Python;
    gui Qt(QWidget);
    options agmagent;
};
~~~

Assuming that you have a file called _agent\_name.cdsl_ in a directory called _agent_name_, you would run the following command to generate the agent's code:
~~~
cd agent_name
robocompdsl agent_name.cdsl .
~~~

Probably the best moment to edit the config file of your component is straight after creating it. There are two main lines that we need to edit:
~~~
AGMCommonBehavior.Endpoints=tcp -p 0
AGMExecutiveProxy = agmexecutive:tcp -h localhost -p 0
~~~
The ports in the previous lines should match the ports in the DSR configuration file. If you followed the example :
~~~
AGMCommonBehavior.Endpoints=tcp -p 11198
AGMExecutiveProxy = agmexecutive:tcp -h localhost -p 10198
~~~


## Modifying the models and subscribing to changes
https://raw.githubusercontent.com/robocomp/robocomp/stable/interfaces/AGMExecutive.ice

Detailed API documentation is hosted in [http://grammarsandrobots.org/AGM/](http://grammarsandrobots.org/AGM/).

## How to set up the whole AGM/CORTEX executive
Even if you want to use AGMExecutive as the whole AGM/CORTEX executive, you should read the section [How to set up a DSR server](#How to set up a DSR server). This section details the steps to make AGGLPlanner work.


## Writing initial models
TO DO
