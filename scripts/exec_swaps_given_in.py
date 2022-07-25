import json
from ape_safe import ApeSafe
from brownie import ZERO_ADDRESS
from eth_abi import encode_single
from brownie import interface, chain
from brownie import Contract, BasketMigrator

HALF_HOUR = 1800
WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
DEV_SAFE_ADDRESS = "0x6458A23B020f489651f2777Bd849ddEd34DfCcd2"

MIGRATOR = "0x7940c0225c836742e8953F69E0af0C4b371a35BF"
ROUTER_UNIV2 = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
ROUTER_SUSHI = "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"
ROUTER_UNIV3 = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
QUOTER_UNIV3 = "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6"
FACTORY_UNIV3 = "0x1F98431c8aD98523631AE4a59f267346ea31F984"

FACTORY_ABI = json.loads('[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint24","name":"fee","type":"uint24"},{"indexed":true,"internalType":"int24","name":"tickSpacing","type":"int24"}],"name":"FeeAmountEnabled","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"oldOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnerChanged","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"token0","type":"address"},{"indexed":true,"internalType":"address","name":"token1","type":"address"},{"indexed":true,"internalType":"uint24","name":"fee","type":"uint24"},{"indexed":false,"internalType":"int24","name":"tickSpacing","type":"int24"},{"indexed":false,"internalType":"address","name":"pool","type":"address"}],"name":"PoolCreated","type":"event"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"}],"name":"createPool","outputs":[{"internalType":"address","name":"pool","type":"address"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"}],"name":"enableFeeAmount","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint24","name":"","type":"uint24"}],"name":"feeAmountTickSpacing","outputs":[{"internalType":"int24","name":"","type":"int24"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"uint24","name":"","type":"uint24"}],"name":"getPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"parameters","outputs":[{"internalType":"address","name":"factory","type":"address"},{"internalType":"address","name":"token0","type":"address"},{"internalType":"address","name":"token1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_owner","type":"address"}],"name":"setOwner","outputs":[],"stateMutability":"nonpayable","type":"function"}]')


def quote_univ2(router, token_in, token_out, amount_in):
    router = interface.IUniswapV2Router01(router)
    try:
        return router.getAmountsOut(amount_in, [token_in, token_out])[1]
    except:
        return 0


def quote_univ2_given_out(router, token_in, token_out, amount_out):
    router = interface.IUniswapV2Router01(router)
    try:
        return router.getAmountsIn(amount_out, [token_in, token_out])[0]
    except:
        return 2**256 - 1


def swap_univ2(router, token_in, token_out, max_in, amount_out, account):
    router = interface.IUniswapV2Router01(router)

    interface.ERC20(token_in).approve(router, max_in, {"from": account})

    router.swapTokensForExactTokens.encode_input(
        amount_out,
        max_in,
        [token_in, token_out],
        account,
        chain.time() + HALF_HOUR,
        {"from": account},
    )


def quote_univ3(factory, quoter, token_in, token_out, amount_in):
    factory = interface.IUniswapV3Factory(factory)
    pool = factory.getPool(token_in, token_out, 3000)

    if pool == ZERO_ADDRESS:
        return 0
    else:
        try:
            quoter = interface.IQuoter(quoter)
            quote = quoter.quoteExactInputSingle.call(
                token_in, token_out, 3000, amount_in, 0
            )

            return quote
        except:
            return 0


def quote_univ3_given_out(factory, quoter, token_in, token_out, amount_out):
    factory = interface.IUniswapV3Factory(factory)
    pool = factory.getPool(token_in, token_out, 3000)

    if pool == ZERO_ADDRESS:
        return 2**256 - 1
    else:
        try:
            quoter = interface.IQuoter(quoter)
            quote = quoter.quoteExactOutputSingle.call(
                token_in, token_out, 3000, amount_out, 0
            )
            return quote
        except:
            return 2**256 - 1


def swap_univ3(router, token_in, token_out, max_in, amount_out, account):
    router = interface.ISwapRouter(router)
    interface.ERC20(token_in).approve(router, max_in, {"from": account})
    router.exactOutputSingle(
        [
            token_in,
            token_out,
            3000,
            account,
            chain.time() + HALF_HOUR,
            amount_out,
            max_in,
            0,
        ]
    )


def main():
    safe = ApeSafe(DEV_SAFE_ADDRESS)
    migrator = safe.contract(MIGRATOR)

    # migrator.burnAndUnwrap({"from": DEV_SAFE_ADDRESS})
    router_univ2 = Contract.from_explorer(ROUTER_UNIV2)
    router_univ3 = Contract.from_explorer(ROUTER_UNIV3)
    router_sushi = Contract.from_explorer(ROUTER_SUSHI)
    quoter_univ3 = Contract.from_explorer(QUOTER_UNIV3)
    factory_univ3 = Contract.from_abi("Factory", FACTORY_UNIV3, FACTORY_ABI)

    

    bdi_assets = [
        "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e",
        "0xc00e94cb662c3520282e6f5717214004a7f26888",
        "0xC011a73ee8576Fb46F5E1c5751cA3B9Fe0af2a6F",
        "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2",
        "0x408e41876cCCDC0F92210600ef50372656052a38",
        "0xdeFA4e8a7bcBA345F687a2f1456F5Edd9CE97202",
        "0xBBbbCA6A901c926F240b89EacB641d8Aec7AEafD",
        "0xba100000625a3754423978a60c9317c58a424e3D",
        "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
        "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
        "0x6B3595068778DD592e39A122f4f5a5cF09C90fE2",
        "0x2ba592F78dB6436527729929AAf6c908497cB200",
        "0x514910771AF9Ca656af840dff83E8264EcF986CA",
        "0x9d409a0A012CFbA9B15F6D4B36Ac57A46966Ab9a",
        "0xE41d2489571d322189246DaFA5ebDe1F4699F498",
    ]

    # exec bdi swaps to eth
    swaps = []
    index = 0 
    for t in bdi_assets:
        token = interface.ERC20(t)
        bal = token.balanceOf("0x0309c98b1bffa350bcb3f9fb9780970ca32a5060")
        univ2_out = quote_univ2(router_univ2, t, WETH, bal)
        sushi_out = quote_univ2(router_sushi, t, WETH, bal)
        univ3_out = quote_univ3(factory_univ3, quoter_univ3, t, WETH, bal)


        print("------------------------------------SWAP ", index, "------------------------------------")
        if univ2_out >= sushi_out and univ2_out >= univ3_out:
            print("Is v3? False")
            print(router_univ2.address, [t, WETH], bal, univ2_out)
            print(encode_single("(address,address[],uint256,uint256)",[router_univ2.address, [t, WETH], bal, univ2_out],).hex())
            swaps.append(
                (
                    False,
                    encode_single(
                        "(address,address[],uint256,uint256)",
                        [router_univ2.address, [t, WETH], bal, univ2_out],
                    ).hex(),
                )
            )
        elif sushi_out >= univ2_out and sushi_out >= univ3_out:
            print("Is v3? False")
            print(router_sushi.address, [t, WETH], bal, sushi_out)
            print(encode_single("(address,address[],uint256,uint256)",[router_sushi.address, [t, WETH], bal, sushi_out]).hex())
            swaps.append(
                (
                    False,
                    encode_single(
                        "(address,address[],uint256,uint256)",
                        [router_sushi.address, [t, WETH], bal, sushi_out],
                    ).hex(),
                )
            )
        else:
            print("Is v3? True")
            print(router_univ3.address, t, WETH, 3000, bal, univ3_out)
            print(encode_single(
                        "(address,address,address,uint24,uint256,uint256)",
                        [
                            router_univ3.address,
                            t,
                            WETH,
                            3000,
                            bal,
                            univ3_out,
                        ],
                    ).hex()
                )
            swaps.append(
                (
                    True,
                    encode_single(
                        "(address,address,address,uint24,uint256,uint256)",
                        [
                            router_univ3.address,
                            t,
                            WETH,
                            3000,
                            bal,
                            univ3_out,
                        ],
                    ).hex(),
                )
            )
    print("\n\n")
    index += 1

    # migrator.execSwaps(swaps, chain.time() + HALF_HOUR, {"from": DEV_SAFE_ADDRESS})

    # weth_erc20 = interface.ERC20(WETH)
    # weth_balance_migrator = weth_erc20.balanceOf(DEV_SAFE_ADDRESS)

    # print(f"weth balance of migrator: {weth_balance_migrator / 1e18}")

    # safe_tx = safe.multisend_from_receipts()

    # safe.preview(safe_tx)
    # safe.sign_with_frame(safe_tx)
    # safe.post_transaction(safe_tx)
