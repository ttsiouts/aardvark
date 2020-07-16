
                       .ho/      -/+
                      hoooy. .+yyod.
                     +yooosdoyooooy+
                     hoooshyossyooss
                     doosdsoy+:yooy+
                     doohyoys::yood
                     yyodooho+soods/////::::--.
                 :hhhhsohoosssosdyssssssssoooossso+/-
                :syoyhsososssoossoooooooooooooooooososo/-
              -ssy/ hddsooh:syooooooooooooooooooooooooooos/-
             +sooos+ohyooy/--yosoooooooooooooooooooooooooooo+
           :soooooooooosho/yoysdooooooooooo+++++ooooooooooooyh
          +soooooooosshyyyssosysoooooooooooo++++oooooooooooooy+
        .ooooooosss+:-. .:yoooooooooooooooooooooosssssssssysooso
       -sooossys+-        :hooooooooooooooooooooosyyssyyssyysooos-
      /soooshs:            /hoooooossssoooooooooooossssyoooosoooos/
     osoosys-               +yoooooossssosssoooooooyyyyyooooyhsoooo+.
    .ssoosy:                  ysooooooossosyyysossssyshyyooooho/ysoooo+.
    yoooss                    sdooohysooooosyyyyssyysysysssyyd   :sssoos+.
    -ysoosy                    :ddyoosh+yssoooosoosooossossssyyy     ./oysoso/-
    o+/ooh                    .hsydoood  -+sysssooooooooodosyyh+         -/+osyyys+
    :+o                       hsosmoood.     -:/+ooosshhhdoossd:
                           :ohysosdoooyo             +hshyooooh:
                            o+sysdhooood           -+ysymoooooh/
                              -/oshsysyh.          .:/+sshyyyyho
                              ::.o/.//               .--:s//o-


# Aardvark

## Purpose

The purpose of this, is to introduce the Reaper [^1] service responsible for
preemptying instances, as proposed by the Nova Team PTG [^2].

The implementation of this prototype service will help to identify changes in
Nova to optimize the feature.

## Prerequisites

### Tagging and Quota

Users should be able to choose if a server is preemptible at creation time. A
limitation of this prototype is that mutable tagging will be used where as the
preemptible property should never change after the creation of the instance.

There are a few aspects for enforcing quota:

* Users who have filled their regular quota want to use preemtible instances
  for additional resources
* There is the need to limit which projects get to use preemtible servers. The
  ideal for this would be a way to limit how many preemptible resources could
  be used on top of the existing quota.

Currently, in Nova, there is no link in between the preemptible tag and the
quota.

#### Initial work

As a starting point and in order to focus on the reaper's functionality, we
are using projects with unlimited quota for resources and control only the
number of preemptible instances that can be spawned by reusing the existing
nova mechanism (instances quota).

This way:
* The servers that belong to this project, will be tagged as preemptibles
  using one of the proposed tagging methods (see below).
* We can limit the usage of preemptible resources for a project. Without
  having set exact limits for each resource class, we can calculate the
  maximum quota for each project with the formula  max_value * instances,
  where:
    * max_value: the maximum value for this resource class in the
                     allocated flavors
    * instances: the number of the allowed instances for this project

Another benefit from this is that there is no need to hack the Nova API to
avoid quota checks just for preemptible VMs.

## WorkFlow

The Reaper service's main duty is to orchestrate Preemptible Servers.
Specifically, it's the reaper's responsibility to select the preemptible
servers that have to be "culled", in order to free up the requested resources
for the creation of non-preemptible instances.

The prototype is a collection of interoperable server tagging methods and
selection strategies. The framework was developed with the logic:

    +----------+              +---------+                +----------+
    | Aardvark |              | Tagging |                | Strategy |
    +----------+              +---------+                +----------+
         |      uses tagging        |                           |
         |------------------------->|                           |
         |  to map servers to hosts |                           |
         |<-------------------------|                           |
         |                          |                           |
         |                  applies | strategy                  |
         |--------------------------|-------------------------->|
         |                to select | servers to cull           |
         |<-------------------------|---------------------------|
         |                          |                           |
         |                          |                           |

The flow of the prototype service is the following

- Triggered by the Scheduler at NoValidHost

  When a boot request for a non-preemptible instance fails due to the fact
  that no valid hosts were returned from Placement API, the Scheduler, sends
  a notification for the failure which triggers Aardvark. The notification
  contains the same resource specifications as the boot request that failed
  in the first place.


- The reaper maps preemptible servers to hosts

  Here the service makes use of the configured tagging method to find the
  preemptible servers in the system. We have implemented two possible
  methods to tag servers as preemptible:

    * Project Tagging

    With this tagging method, the preemptible property resides in the project
    where the servers belong to. As a result all servers that belong to a
    preemptible project, are preemptible too. The Reaper requests from
    Keystone the projects with this property, gathers the servers that belong
    to each of these projects and maps them per host.

    $ openstack project set --tag preemptible preemptible_project


    * Resource Tagging (Alternative)

    By exposing a custom resource class and making use of the Nested Resource
    providers concept, we can place a granular request to Placement when a
    preemptible server is spawning, requesting allocations to the custom
    resource class too:

    $ openstack flavor set --property resources(N):CUSTOM_PREEMPTIBLE='1' ...
    e.g. /allocation_candidates?resources=...resources(N)=CUSTOM_PREEMPTIBLE:1

    So all the preemptible servers, will be tagged with the custom resource
    class we exposed. This way we transfer the information for the preemptible
    servers to the Placement.

    For this and under the scope of this prototype, we introduced the route
    "/culling_candidates" to the Placement API. The reaper service places the
    same request as the scheduler does, when asking for allocation candidates.
    The GET request looks like this:
    /culling_candidates?resources=VCPU:1,MEMORY_MB:2048,DISK_GB:20

    In fact, the query is almost the same with the allocation candidates. The
    only difference in the resulting DB query can be seen below:

    Allocation Candidates
    For each requested resource class:
        rc_usage + rc_requested <= rc_total

    Culling Candidates
    For each requested resource class:
        rc_usage + rc_requested - rc_preemptible_usage  <= rc_total

    The API responds in the following way:

    ```
        'provider_summaries': {
            '$rp_uuid': {
                'resources': {
                    '$requested_rc1': {u'used': ..., 'capacity': ...},
                    ...
                }
            }
            ....
        }
        'preemptible_allocations': {
             '$rp_uuid’: {
                 '$consumer_uuid1': {
                     '$requested_rc1': $consumed_amount
                     ...
                     'CUSTOM_PREEMPTIBLE': 1
                 }
                 '$consumer_uuid2': {
                     '$requested_rc1': $consumed_amount
                     ...
                     'CUSTOM_PREEMPTIBLE': 1
                 }
                 ...
             }
             ...
        }
    ```

    **Note:** Although, this was implemented as PoC, we chose to go with the project
              tagging since the changes in Placement/Nova side are significant.


- Strategies for selecting preemptibles

  The strategies are the different ways that the reaper will try to free up
  the requested resources.

  Currently we have three strategies (drivers) for selecting instances:

    * chance driver
        A valid host is selected randomly and in a number of preconfigured
        retries, the driver tries to find the instances that have to be culled
        in order to have the requested resources available.

    * strict driver
        The purpose of the preemptibles existence is to eliminate the idling
        resources. This driver gets all the possible offers from the relevant
        hosts and tries to find the best matching for the requested resources.
        The best matching offer is the combination of preemptible servers that
        leave the least possible resources unused.

    * strict_time driver
        Same as strict, but preemptible servers are sorted based on creation
        time.

  In a rapidly changing cloud environment, there might be races between the
  time we get the snapshot of hosts and the time we try to free up the
  requested resources. So, following the concecpt of allocation alternatives,
  we introduced the culling alternatives. The operator can configure a number
  of alternative slots to be freed up for each requested slot. Effectively
  the service will try to free up:

        * maximum: requested slots * alternative slots (per instance)
        * minimum: requested slots

  If the configured driver, doesn't find a way to free up at least the minimum
  amount of slots, no server is returned to the Reaper, meaning that no server
  is terminated.


- "Culling" Preemptible Instances

  The reaper service places delete server requests to the Nova API, in order
  to terminate the preemptible servers, selected for "culling".


### Scenarios

#### Booting a Preemptible Server

As mentioned, the preemptible project will have unlimited quota for the
resource classes and the user has limited number of instances to spawn.

##### Resources available

(Trivial) Since there are available resources, booting a server is expected to
succeed.

##### No resources available

(Trivial) While booting a preemptible server, if the Placement API returns no
valid candidate host, then the procedure fails. No request is placed to the
reaper in this case.

#### Booting a Non-Preemptible Server

Quota accounting is applied for the non-preemptible servers, so a project's
quota has to not be exceeded in order to have the ability to boot a server
successfully.

##### Resources available

(Trivial) Since there are available resources, booting a server is expected to
succeed.

##### No resources available

- Since there are no available resources, the Placement API returns no valid
  candidates for hosting the new Server.
- At this time, Nova sends a notification to the configured RabbitMQ. Aardvark
  is subscribed to the queue and it gets triggered to free up the resources
  needed for the non-preemptible server.
- The reaper service selects the preemptible servers using one of the
  strategies above (configuration option) and proceeds with their deletion.

## References

   [^1]: https://www.youtube.com/watch?v=ClQcUyhoxTg
   [^2]: http://lists.openstack.org/pipermail/openstack-dev/2017-September/122258.html
