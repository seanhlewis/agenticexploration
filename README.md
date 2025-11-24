# Agentic Exploration in Games

<img width="1600" alt="agentic_exploration_header" src="https://github.com/user-attachments/assets/481dcd73-63db-4ab6-8616-4d736dfdc79e" />

Agentic exploration in games aims to revolutionize 3D game environments by leveraging Tesla FSD inspired 3D occupancy grid algorithms. With an emphasis on voxel based games like Minecraft, this research bridges real time world knowledge and AI navigation, laying a foundation for agents to interact with dynamically learned environments. This work is critical to improving diffusion based gaming systems and enabling more consistent, meaningful agent guided exploration.

I am interested in what happens when game agents stop relying only on hand authored navigation meshes or static maps, and instead build and update a live world model similar to what an autonomous vehicle might use. This is my attempt to pull ideas from real world robotics, SLAM, and 3D occupancy reasoning into virtual, interactive environments.

---

## Motivation

This project started with a simple question: what if the same ideas used to help self driving cars understand roads in real time could also help AI agents navigate complex 3D worlds in video games?

I have always been fascinated by voxel based games like Minecraft, where environments can be enormous and ever changing. Unlike many traditional games, a Minecraft world can be carved, rebuilt, and reimagined by players at any moment. That makes static navigation tools feel brittle. If the world changes and the AI does not update its understanding, the agent quickly looks fake.

In parallel, 3D occupancy grid methods from Tesla style full self driving systems and work like OccRWKV show how powerful it is to maintain a dense, semantic representation of the world in real time. We started asking: what if we brought that kind of representation into games, and let agents think in terms of occupancy instead of just waypoints.

At the same time, diffusion based models are starting to show up in gaming contexts for things like texture generation, style transfer, and scene editing. If a diffusion model and an agent shared the same structural map of the world, could they stay in sync as both the visuals and the behavior evolve.

The high level question behind this project became: what happens when an AI agent in a game and a diffusion model that renders the world both share the same underlying map of reality.

<p align="center">
  <img height="320" src="https://github.com/user-attachments/assets/92f54294-e7a3-486e-bcfa-099bb050e572" alt="Intelligent Agents Example">
</p>

---

## High Level Idea

At a high level, Agentic Exploration in Games has two intertwined objectives:

1. Real time 3D occupancy grids for game AI.  
2. Integration of those grids with diffusion based gaming systems.

We integrate semantic 3D occupancy grids with diffusion models, enabling real time agent navigation in games and improving game diffusion consistency by leveraging learned worlds. Instead of treating each frame as an isolated image, we treat the game world as a structured, evolving 3D map that both agents and generative models can reference.

The core research goal can be summarized as:

> Integrate semantic 3D occupancy grids with diffusion models, enabling real time agent navigation in games, improving game diffusion consistency by leveraging learned worlds.

In other words: give agents and generative models the same shared world model, and see what new behaviors and experiences that unlocks.

<p align="center">
  <img height="320" src="https://github.com/user-attachments/assets/6f0f63a4-0ecd-45cc-a668-410635c885c8" alt="High level diagram of Agentic Exploration in Games">
</p>

This diagram illustrates how Minecraft gameplay, voxel extraction, occupancy grid construction, and AI agents fit together with diffusion models and downstream experiments. 

---

## Minecraft Testbed and 6 DoF Dataset

Using Minecraft as a testbed, I developed a pipeline to collect six degrees of freedom screenshots and voxel level ground truth block data using Minescript and Anvil. Each data point contains:

- A 6 DoF camera pose.  
- A high resolution screenshot from that pose.  
- Voxel level block labels in a region around the player.

This design lets us build a labeled gameplay dataset at 6 DoF that feels very similar to real world sensor datasets, but in a completely controllable environment.

From this data, we can construct real time 3D occupancy grids. These grids answer simple but powerful questions such as:

- Is this region of space free or occupied.  
- What type of block or semantic label lives here.  
- How has this region changed over time as players build or destroy structures.

The occupancy grid serves as a live memory of the environment that the agent can query at any time. In robotics, this links back to ideas from SemanticKITTI and other LiDAR based mapping work. Here, the sensors are virtual, but the underlying problem of consistent 3D understanding is the same.

Preliminary results demonstrate the effectiveness of our 6 DoF screenshot collection and voxel extraction for creating a robust Minecraft dataset. Collected datasets are successfully trained with real time occupancy grids, showcasing accurate scene reconstruction and labeling. We can reconstruct views of the world from new poses using only the occupancy grid and semantic labels, which shows that the representation captures enough structure to be useful.

<p align="center">
  <img height="320" src="https://github.com/user-attachments/assets/cfc326c8-1e22-4f8f-ba4b-4264a6cf40c0" alt="SLAM Visualization Example">
</p>

Here, we visualize a SLAM style reconstruction with 2D and 3D views of the environment. Even though the sensor is a virtual camera and block sampler instead of LiDAR, the resulting map behaves a lot like the maps used in autonomous driving. 

---

## Methods and Pipeline Details

The core pipeline is divided into two major parts: Minecraft occupancy learning and diffusion based gaming.

### Minecraft occupancy pipeline

For Minecraft, we use Minescript and Anvil to interface with the world data. The pipeline looks like this:

1. Sample camera poses with six degrees of freedom within a region of the Minecraft world.  
2. Capture a screenshot from each pose.  
3. Extract the surrounding voxel map using Anvil, generating block level ground truth.  
4. Convert the block world into a semantic occupancy grid representation aligned with the camera pose.  
5. Train models that predict occupancy and semantics from images and pose, and refine the grid over time during gameplay.

The occupancy grid is updated as the player or agent moves. When new information contradicts older beliefs, the grid is updated so that agents always query the most consistent view available.

I like to think of this as giving the agent a memory that is physically grounded rather than just a history of actions.

### Diffusion gaming with Dust 2

For diffusion gaming, I adapted CS:GO Dust 2 footage to modify diffusion pipelines using Image to Image guidance. Instead of treating each frame as an independent image, we treat it as a slice of a consistent environment.

The process is as follows:

We collect gameplay footage from Dust 2, focusing on sequences where the player revisits the same areas from different angles. We then modify Diamond Diffusion pipelines to introduce contour guided diffusion. Structural contours, map boundaries, and layout hints act as anchors for the generative model.

Initial experiments on Dust 2 confirm that modifying Diamond Diffusion pipelines can introduce consistent contour guided diffusion, by redirecting the player to consistent locations when frames are joined with similar frames of learned locations. This starts to feel like a kind of imaginative SLAM: the model fills in textures or styles, but still respects the layout of the world.

My process facilitates real time parallel pipelines that process and overlay 3D style contours on top of 2D frames. Even when the underlying footage is standard gameplay, the generated variations can remain geographically grounded.

Video of Minecraft agentic exploration:

https://github.com/user-attachments/assets/64c77774-36d6-4340-a227-17c32e6db12d

---

## Observations

We found that the occupancy grid approach helped AI agents maintain a more consistent view of the world, particularly as chunks, sections of the game, loaded or unloaded. In Minecraft, distant chunks may appear or disappear depending on view distance and performance constraints. Without a persistent world model, an agent might treat these events as strange teleportations.

With an occupancy grid, the agent can reconcile these changes. When a chunk becomes visible again, the model can check whether the structure has changed and update its beliefs accordingly. Agents navigated more confidently across diverse terrain and could adapt to sudden changes such as a new building appearing where there was once open space.

This method also reduced impossible or awkward movements. Because the grid explicitly marks filled regions, the planner can avoid asking the agent to walk through walls, stand inside blocks, or take paths that clip through the environment. As a result, navigation feels less like a hack and more like a consequence of how the world is actually represented.

On the diffusion side, occupancy style guidance reduced some of the classic failure modes of generative models that operate frame by frame. Instead of drifting into new layouts with each frame, the model had a structural scaffold to respect. It could still change textures, lighting, and stylistic elements, but core landmarks stayed aligned. This is particularly noticeable when moving through a map like Dust 2 where players subconsciously expect consistent corridors, doors, and sightlines.

---

## Discussion

Agentic exploration in games sits at the intersection of three ideas: semantic SLAM, voxel based worlds, and generative diffusion models. Real time 3D occupancy grids provide a bridge between what agents perceive and what generative models create.

From an AI agent perspective, the project reinforces a simple point: agents look smarter when they have good world models. Even in a controlled environment like Minecraft, arbitrary scripts that ignore persistent structure feel flimsy. By giving the agent a dense, semantic representation of space, we make it easier to reason about visibility, obstacles, and opportunities.

From a generative modeling perspective, the project suggests that diffusion based gaming systems can benefit from occupancy information. Instead of asking a model to imagine each frame from scratch, we can ask it to decorate or transform a known 3D layout. That shifts the model's job from "invent the world" to "stylize the world," which is more consistent with how players think about game levels.

We could also ask more playful questions. What if an agent could request a new cave system to be generated in an unoccupied region, then immediately explore it using the same occupancy grid that inspired its creation. What if a diffusion model could "dream up" an alternate version of Dust 2, but still output something navigable and tactically coherent.

From a research framing perspective, this work hints at what it might mean to build next generation AI gaming frameworks. If both decision making and rendering share the same structural backbone, then new kinds of agent guided exploration become possible.

---

## Conclusion and Future Work

This research demonstrates the potential to combine occupancy grids with diffusion models for enhanced 3D navigation and gaming systems. I see agentic exploration in games as an early step toward AI agents that live inside worlds they continuously learn and reconstruct.

Future work will extend to open source diffusion gaming models, adding real time 3D occupancy overlays for improved agent environment interaction. I particularly would like to explore:

- Direct coupling between OccRWKV style occupancy predictors and diffusion backbones.  
- Larger Minecraft and Dust 2 datasets that more closely mirror SemanticKITTI scale.  
- User studies that test how players perceive agents that rely on learned maps versus agents that move along traditional scripted paths.  
- More ambitious imaginative SLAM setups where the model hallucinates new regions but still stitches them into a coherent global map.

By merging real world mapping with gaming, I hope to help pave the way for next generation AI gaming frameworks that feel both more intelligent and more playful.

---

## Acknowledgments

I thank Cornell Tech and Bowers CIS for their support, as well as the open source contributors to tools like Minescript, Anvil, OccRWKV, and Diamond Diffusion. Special thanks to the SemanticKITTI team for their dataset framework, which strongly influenced how I thought about temporal sequences of 3D scenes. I am also grateful to all mentors and peers for their valuable feedback on both the technical design and the broader framing of this work.

---

## References

Behley, J., et al. SemanticKITTI: Semantic Scene Understanding of LiDAR Sequences. ICCV, 2019.  
Wang, J., et al. OccRWKV: Real Time 3D Occupancy Grid. GitHub.  
Alonso, E., et al. Diamond Diffusion: Contour Guided Translation. GitHub.  
