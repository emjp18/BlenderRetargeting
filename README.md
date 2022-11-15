# BlenderRetargeting

A work in progress.

#Functions
The Read File function takes in a text file where you can map bones so you don't have to use the editor. It only uses it if it can read it and finds matching names and you can still edit after its been loaded.

Change orientation aims to change the bones so they have the same direction and roll as the source skeleton bones. It takes in the normalized direction from the source skeleton bone, takes the cross of the target bone direction to get an axis and arcos to get an angle, since editbones change due to their parents it goes from the root to the children in that order.

Calcfinalmatrix calcultes the transformation for each bone at each frame, it converts from bone space to world space to the target bone space. I use blenders own functions instaead of complicated math. I only use the rotation except for the root bone that also uses translation. But scale is ommitted.

Getparentchains is used for the orientationcorrection it creates index listt Every bone has a list of a chain.

CalcOrientationandRotation calculates bindpose matrices and rotation matrices of each frame this is not needed to be done at runtime so its done once and then stored to be used later. Only the source skeleton has rotation of each frame.

Choose source marks the source skeleton, should be used before choosing target. It also fetches keyframedata, so choose a range before using this.

Choose target marks the target skeleton and fills a dictionary with mappings.

You can map any source bone to any target bone or nullify any bone.


#Current problems
Some skeletons are not very comaptible so it would be nice to offset the bones somehow.




