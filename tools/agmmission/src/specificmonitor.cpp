/*
 *    Copyright (C) 2010 by RoboLab - University of Extremadura
 *
 *    This file is part of RoboComp
 *
 *    RoboComp is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU General Public License as published by
 *    the Free Software Foundation, either version 3 of the License, or
 *    (at your option) any later version.
 *
 *    RoboComp is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU General Public License for more details.
 *
 *    You should have received a copy of the GNU General Public License
 *    along with RoboComp.  If not, see <http://www.gnu.org/licenses/>.
 */
#include "specificmonitor.h"
#include "specificworker.h"

int32_t strToNumber(const std::string &s)
{
	if (s.size()<=0)
	{
		throw 1;
	}

	int32_t ret;
	std::string str = s;
	//replace(str.begin(), str.end(), ',', '.');
	std::istringstream istr(str);
	istr.imbue(std::locale("C"));
	istr >> ret;
	return ret;
}

vector<std::string> commaSplit(const std::string &s)
{
	stringstream ss(s);
	vector<string> result;

	while (ss.good())
	{
		string substr;
		getline( ss, substr, ',' );
		result.push_back( substr );
	}
	return result;
}

/**
* \brief Default constructor
*/
SpecificMonitor::SpecificMonitor(GenericWorker *_worker,Ice::CommunicatorPtr _communicator):GenericMonitor(_worker, _communicator)
{
	ready = false;
}
/**
* \brief Default destructor
*/
SpecificMonitor::~SpecificMonitor()
{
	std::cout << "Destroying SpecificMonitor" << std::endl;
}

void SpecificMonitor::run()
{
	initialize();
	ready = true;
	forever
	{
		//rDebug("specific monitor run");
		this->sleep(period);
	}
}

/**
 * \brief Reads components parameters and checks set integrity before signaling the Worker thread to start running
 *   (1) Ice parameters
 *   (2) Local component parameters read at start
 *
 */
void SpecificMonitor::initialize()
{
	rInfo("Starting monitor ...");
	initialTime=QTime::currentTime();
	RoboCompCommonBehavior::ParameterList params;
	readPConfParams(params);
	readConfig(params);
	if(!sendParamsToWorker(params))
	{
		rError("Error reading config parameters. Exiting");
		killYourSelf();
	}
	state = RoboCompCommonBehavior::State::Running;
	emit initializeWorker(period);
}

bool SpecificMonitor::sendParamsToWorker(RoboCompCommonBehavior::ParameterList params)
{
	if(checkParams(params))
	{
		//Set params to worker
		if(worker->setParams(params)) 
			return true;
	}
	else
	{
		rError("Incorrect parameters");
	}
	return false;

}

///Local Component parameters read at start
///Reading parameters from config file or passed in command line, with Ice machinery
///We need to supply a list of accepted values to each call
void SpecificMonitor::readConfig(RoboCompCommonBehavior::ParameterList &params )
{
    printf("agmmission::run()\n");
	int32_t goals;
	vector<std::pair<std::string, std::string> > missions;
	try
	{
		string goals_st;
		configGetString( "","Goals", goals_st, "");
		goals = strToNumber(goals_st);
		printf("Goals: %d\n", goals);
		for (int32_t i=0; i<goals; i++)
		{
			printf("iteration %d\n", i);
			std::ostringstream ostr;
			ostr.imbue(std::locale("C"));
			ostr << "Goal";
			ostr << i + 1;
			std::string goalDescriptor;
			std::string xxp;
			printf("Variable to read %s\n", ostr.str().c_str());
 			configGetString("", ostr.str(), xxp, "");
			printf("got string %s\n", xxp.c_str());
			vector<std::string> result = commaSplit(xxp);
			printf("parts %d\n", (int)result.size());
			missions.push_back(std::pair<std::string, std::string>(result[0], result[1]));
			printf("%s: <%s> <%s>\n", ostr.str().c_str(), result[0].c_str(), result[1].c_str());
		}
	}
	catch(...)
	{
		fprintf(stderr, "Can't read 'Goals' configuration variable (needed to set the goals of the mission controller.\n");
		exit(42);
	}

	std::string stopMission;
	try
	{
        configGetString("", "GoalStop", stopMission, "");
	}
	catch(...)
	{
		fprintf(stderr, "Can't read 'GoalStop' configuration variable (needed to set the goals of the mission controller.\n");
		exit(42);
	}

	for (uint32_t i=0; i<missions.size(); i++)
	{
		((SpecificWorker*)worker)->addMission(missions[i].first, missions[i].second);
	}
	printf("Stop mission: %s\n", stopMission.c_str());
	((SpecificWorker*)worker)->setStopMission(stopMission);
    
    
	//	RoboCompCommonBehavior::Parameter aux;
//	aux.editable = true;
//	configGetString( "","InnerModelPath", aux.value, "nofile");
//	params["InnerModelPath"] = aux;
}

//Check parameters and transform them to worker structure
bool SpecificMonitor::checkParams(RoboCompCommonBehavior::ParameterList l)
{
	bool correct = true;
	return correct;
}

