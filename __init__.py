from __future__ import division  # Use floating point for math calculations

import types
import math

from CTFd.models import Solves, db
from CTFd.plugins.challenges import CHALLENGE_CLASSES
from CTFd.utils.modes import get_model

'''
const p0 = 0.7
const p1 = 0.96

const c0 = -Math.atanh(p0)
const c1 = Math.atanh(p1)
const a = (x: number): number => (1 - Math.tanh(x)) / 2
const b = (x: number): number => (a((c1 - c0) * x + c0) - a(c1)) / (a(c0) - a(c1))

export const getScore = (rl: number, rh: number, maxSolves: number, solves: number): number => {
  const s = Math.max(1, maxSolves)
  const f = (x: number): number => rl + (rh - rl) * b(x / s)
  return Math.round(Math.max(f(solves), f(s)))
}
'''



def calculate_value(cls, challenge):
    Model = get_model()

    solve_count = (
        Solves.query.join(Model, Solves.account_id == Model.id)
        .filter(
            Solves.challenge_id == challenge.id,
            Model.hidden == False,
            Model.banned == False,
        )
        .count()
    )

    # If the solve count is 0 we shouldn't manipulate the solve count to
    # let the math update back to normal
    if solve_count != 0:
        # We subtract -1 to allow the first solver to get max point value
        solve_count -= 1

    # It is important that this calculation takes into account floats.
    # Hence this file uses from __future__ import division
    p0 = 0.7
    p1 = 0.96
    c0 = -math.atanh(p0)
    c1 = math.atanh(p1)
    a = lambda x: (1 - math.tanh(x)) / 2
    b = lambda x: (a((c1 - c0) * x + c0) - a(c1)) / (a(c0) - a(c1))

    def get_score(rl, rh, maxSolves, solves):
        s = math.max(1, maxSolves)
        f = lambda x: rl + (rh - rl) * b(x / s)
        return round(math.max(f(solves), f(s)))
    value = get_score(challenge.minimum, challenge.initial, challenge.decay, solve_count)

    if value < challenge.minimum:
        value = challenge.minimum

    challenge.value = value
    db.session.commit()
    return challenge


def load(app):
    dvc_class = CHALLENGE_CLASSES["dynamic"]
    print("hooking DynamicValueChallenge and modifying calculate method...")
    setattr(dvc_class, calculate_value.__name__, types.MethodType(calculate_value, dvc_class))
