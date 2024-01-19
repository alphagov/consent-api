#!/bin/sh

echo "Are you sure you want to publish the package to npm? Type YES to confirm."
read confirmation

if [ "$confirmation" = "YES" ]; then
    npm run build && npm publish
else
    echo "Publish cancelled."
fi
